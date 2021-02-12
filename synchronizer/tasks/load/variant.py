from django_bulk_update.helper import bulk_update
from oscar.apps.catalogue.models import Product, ProductClass
from oscar.core.loading import get_model

from synchronizer.models import ProductSync, VariantSync
from synchronizer.utils.loader import RequestList
from synchronizer.tasks.load.product import default_url as product_default_url
from synchronizer.tasks.load.product import update_product_attr_from_sync_obj, \
    delete_price, update_price_product_from_sync_obj
from synchronizer.utils.optional import Optional
from synchronizer.utils.util import get_map_objects_by_id_element_row, \
    parse_date_for_moscow, update_or_insert

ProductInformation = get_model('shop', 'ProductInformation')

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/variant/"


def execute(last_update=None):
    product_sync_ids = list(ProductSync.objects.values_list('sync_id', flat=True))

    variant_rows = []
    params = {}
    if last_update:
        params['updatedFrom'] = last_update.strftime('%Y-%m-%d %H:%M:%S')

    variant_rows.extend(RequestList.load_rows_by_url(default_url, params=params))
    variant_product_in_db = list(filter(lambda x: Optional(x.get('product')).map(lambda x: x.get('meta'))
                                        .map(lambda x: x.get('href'))
                                        .if_exists(lambda x: x.replace(product_default_url, '')) in product_sync_ids,
                                        variant_rows))
    update_pv(variant_product_in_db)


def update_pv(variant_load_rows):
    variant_obj = []

    pv_by_sync_id_dict = get_map_objects_by_id_element_row(
        variant_load_rows,
        lambda sync_ids: VariantSync.objects.get_by_sync_ids(sync_ids))

    for row in variant_load_rows:
        sync_id = row.get('id')
        pv_from_db = pv_by_sync_id_dict.get(sync_id) if pv_by_sync_id_dict.get(sync_id) else VariantSync()

        product_id = Optional(row.get('product')).map(lambda x: x.get('meta')) \
            .map(lambda x: x.get('href')).if_exists(lambda x: x.replace(product_default_url, ''))
        price = Optional(row.get('salePrices')).map(lambda x: x[0]).map(lambda x: x.get('value')) \
            .if_exists(lambda x: x / 100)

        updated_date = parse_date_for_moscow(row.get('updated'))

        pv_from_db.sync_id = sync_id
        pv_from_db.product_sync_id = product_id
        pv_from_db.archived = row.get('archived')
        pv_from_db.updated = updated_date
        pv_from_db.name = row.get('name')
        pv_from_db.price = price

        pv_from_db.set_characteristics(({attr.get('name'): attr.get('value')
                                         for attr in row.get('characteristics')}) if row.get(
            'characteristics') else None)
        variant_obj.append(pv_from_db)

    result_variant = update_or_insert(variant_obj, VariantSync.objects)

    update_product(result_variant)


def update_product(variants):
    product_class = ProductClass.objects.get_or_create(name='moy_sklad_child')[0]
    sync_ids = list(map(lambda x: x.product_sync_id, variants))
    product_syncs = list(ProductSync.objects.filter(sync_id__in=sync_ids))
    delete_price(product_syncs)
    product_sync_map_by_sync = {product_sync.sync_id: product_sync for product_sync in product_syncs}
    parents = set()
    for variant in variants:
        product_sync = product_sync_map_by_sync.get(variant.product_sync_id)
        parent_product = product_sync.product
        if parent_product:
            product = variant.product if variant.product else Product()
            product.is_discountable = True
            # product.product_class = product_class
            product.product_class = None
            product.title = product_sync.name
            product.parent = parent_product
            product.structure = Product.CHILD
            product.save()
            obj, created = ProductInformation.objects.update_or_create(
                product=product, defaults={'hide': variant.archived})
            variant.product = product

            parent_product.structure = Product.PARENT
            parents.add(parent_product)

    VariantSync.objects.bulk_update(variants)
    bulk_update(parents)

    update_product_attr_from_sync_obj(variants, lambda x: x.get_characteristics(), product_class)
    update_price_product_from_sync_obj(variants)
