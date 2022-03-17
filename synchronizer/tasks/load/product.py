import json
import os
import requests

from django.conf import settings
from django_bulk_update.helper import bulk_update
from oscar.apps.catalogue.models import Product, ProductClass, ProductAttribute, ProductAttributeValue, \
    ProductCategory, ProductImage
from oscar.apps.partner.models import StockRecord, Partner
from oscar.core.loading import get_model

from synchronizer.models import ProductFolderSync, ProductSync
from synchronizer.tasks.load import product_folder
from synchronizer.utils.loader import RequestList
from synchronizer.utils.optional import Optional
from synchronizer.utils.util import get_map_objects_by_id_element_row, \
    parse_date_for_moscow, update_or_insert, bulk_save

ProductInformation = get_model('shop', 'ProductInformation')

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/product/"
DIR_PATH = os.path.join(settings.MEDIA_ROOT, settings.MOYSKLAD_MEDIA_URL)

attr_type_enum = {
    'customentity':
        (lambda attr: Optional(attr).map(lambda x: x.get('value')).if_exists(lambda x: x.get('name'))),
    'long':
        (lambda attr: Optional(attr).if_exists(lambda x: x.get('value'))),
    'string':
        (lambda attr: Optional(attr).if_exists(lambda x: x.get('value'))),
    'text':
        (lambda attr: Optional(attr).if_exists(lambda x: x.get('value'))),
    "product": (
        lambda attr: Optional(attr)
            .map(lambda x: x.get("value", {}).get('meta'))
            .if_exists(lambda x: x.get("href", "").replace(default_url, ""))
        )
}

partner_sku_func = lambda partner, product: 'par=' + str(partner.id) + '_prod=' + str(product.id)


def execute(last_update=None):
    params = {}

    if last_update:
        params['updatedFrom'] = last_update.strftime('%Y-%m-%d %H:%M:%S')

    products_rows = RequestList.load_rows_by_url(default_url, params=params)
    update_p(products_rows)


def update_p(product_rows):
    product_objs = []

    p_by_sync_id_dict = get_map_objects_by_id_element_row(
        product_rows,
        lambda sync_ids: ProductSync.objects.get_by_sync_ids(sync_ids))

    for row in product_rows:
        sync_id = row.get('id')
        p_from_db = p_by_sync_id_dict.get(sync_id) if p_by_sync_id_dict.get(sync_id) else ProductSync()

        product_folder_id = Optional(row.get('productFolder')).map(lambda x: x.get('meta')) \
            .map(lambda x: x.get('href')).if_exists(lambda x: x.replace(product_folder.default_url, ''))
        price = Optional(row.get('salePrices')).map(lambda x: x[0]).map(lambda x: x.get('value')) \
            .if_exists(lambda x: x / 100)
        updated_date = parse_date_for_moscow(row.get('updated'))

        if not product_folder_id:
            continue

        p_from_db.sync_id = sync_id
        p_from_db.folder_sync_id = product_folder_id
        p_from_db.path_name = row.get('pathName')
        p_from_db.archived = row.get('archived')
        p_from_db.updated = updated_date
        p_from_db.name = row.get('name')
        p_from_db.article = row.get('article')
        p_from_db.description = row.get('description')

        p_from_db.volume = row.get('volume')
        p_from_db.weight = row.get('weight')
        p_from_db.price = price
        p_from_db.image_url = Optional(row.get('image')).map(lambda x: x.get('meta')) \
            .map(lambda x: x.get('href')).if_exists(lambda x: x)

        p_from_db.set_attributes(({attr.get('name'): attr_type_enum.get(attr.get('type'))(attr)
                                   for attr in row.get('attributes')}) if row.get('attributes') else None)

        product_objs.append(p_from_db)

    result = update_or_insert(product_objs, ProductSync.objects)
    update_product(result)


def update_product(product_syncs):
    if not os.path.exists(DIR_PATH):
        os.makedirs(DIR_PATH)

    product_class = ProductClass.objects.get_or_create(name='moy_sklad')[0]
    sync_ids = list(map(lambda x: x.folder_sync_id, product_syncs))
    pf_syncs = list(ProductFolderSync.objects.filter(sync_id__in=sync_ids))
    pf_sync_map_by_sync = {pf_sync.sync_id: pf_sync for pf_sync in pf_syncs}

    for product_sync in product_syncs:
        pf_sync = pf_sync_map_by_sync.get(product_sync.folder_sync_id)
        product = product_sync.product if product_sync.product else Product()
        product.is_discountable = True
        product.product_class = product_class
        product.title = product_sync.name
        product.description = product_sync.description if product_sync.description is not None else ''
        if Product.objects.exclude(id=product.id).filter(upc=product_sync.article).exists():
            Product.objects.exclude(id=product.id).filter(upc=product_sync.article).update(upc=None)
        product.upc = product_sync.article
        product.save()
        product.children.update(title=product_sync.name)
        obj, created = ProductInformation.objects.update_or_create(
            product=product, defaults={'hide': product_sync.archived})

        attributes = json.loads(product_sync.attributes)

        care_description = attributes.get('Уход', '')

        information, _ = ProductInformation.objects.get_or_create(product=product)
        information.care_description = care_description
        information.save()

        if product_sync.image_url is not None:
            img_name = product_sync.image_url.replace('https://online.moysklad.ru/api/remap/1.1/download/', '')
            img_path = os.path.join(settings.MEDIA_ROOT, settings.MOYSKLAD_MEDIA_URL + '/' + img_name + '.jpg')

            origin = settings.MOYSKLAD_MEDIA_URL + '/' + img_name + '.jpg'
            image = ProductImage.objects.filter(original=origin, product=product).first()
            if not image:
                p = requests.get(product_sync.image_url,
                                 headers={'Authorization': 'Basic ' + settings.MOYSKLAD_TOKEN})
                out = open(img_path, "wb")
                out.write(p.content)
                out.close()
                ProductImage.objects.filter(product=product).delete()
                image = ProductImage(product=product, original=origin)
                image.save()

        for category in list(product.categories.all()):
            if category != pf_sync.category:
                ProductCategory.objects.filter(category=category, product=product).delete()
        ProductCategory.objects.get_or_create(category=pf_sync.category, product=product)

        product_sync.product = product

    ProductSync.objects.bulk_update(product_syncs)

    update_product_attr_from_sync_obj(product_syncs, lambda x: x.get_attributes(), product_class)
    update_price_product_from_sync_obj(product_syncs)


def update_product_attr_from_sync_obj(product_syncs, get_attributes_func, product_class):
    attr_keys = set().union(*map(lambda x: list(get_attributes_func(x).keys()), product_syncs))
    attr_map = {}

    for attr_key in attr_keys:
        attr = \
            ProductAttribute.objects.get_or_create(product_class=product_class,
                                                   name=attr_key, code=attr_key, type='text')[0]
        attr_map[attr.code] = attr

    attrs = attr_map.values()
    products = list(map(lambda x: x.product, product_syncs))
    attr_values = list(ProductAttributeValue.objects.filter(attribute__in=attrs, product__in=products))
    attr_values_map = {(attr.product.id, attr.attribute.id): attr for attr in attr_values}

    added_attr_values = []
    updated_attr_values = []
    deleted_attr_value_ids = []
    for product_sync in product_syncs:
        product = product_sync.product

        product_attr_values = []
        for key, value in get_attributes_func(product_sync).items():
            attr = attr_map.get(key)

            attr_value = attr_values_map.get((product.id, attr.id))
            attr_value = attr_value if attr_value else ProductAttributeValue(product=product, attribute=attr)
            attr_value.value_text = value
            # attr_value.save()
            if attr_value.id is None:
                added_attr_values.append(attr_value)
            else:
                updated_attr_values.append(attr_value)
            product_attr_values.append(attr_value)

        for deleted_attr in \
                list(product.attribute_values.exclude(id__in=list(map(lambda x: x.id, product_attr_values)))):
            deleted_attr_value_ids.append(deleted_attr.id)
            # deleted_attr.delete()
    update_result = bulk_update(updated_attr_values)
    if getattr(settings, 'MOYSKLAD_BULK_CREATE', True):
        insert_result = ProductAttributeValue.objects.bulk_create(added_attr_values)
    else:
        insert_result = bulk_save(added_attr_values)
    delete_result = ProductAttributeValue.objects.filter(id__in=deleted_attr_value_ids).delete()


def update_price_product_from_sync_obj(product_syncs):
    products = list(map(lambda x: x.product, product_syncs))
    partners = list(Partner.objects.all())
    stock_records = list(StockRecord.objects.filter(product__in=products, partner__in=partners))
    product_stock_map = {str(stock_record.product.id) + '_' + str(stock_record.partner.id): stock_record
                         for stock_record in stock_records}
    updated_stock_records = []
    added_stock_records = []
    for product_sync in product_syncs:
        for partner in partners:
            product = product_sync.product
            stock_record = product_stock_map.get(str(product.id) + '_' + str(partner.id))
            if stock_record:
                stock_record.price_excl_tax = product_sync.price if product_sync.price else 0
                stock_record.price_retail = product_sync.price
                # stock_record.save()
                updated_stock_records.append(stock_record)
            else:
                stock_record = StockRecord(product=product, partner=partner)
                stock_record.partner_sku = partner_sku_func(partner, product)
                stock_record.price_excl_tax = product_sync.price if product_sync.price else 0
                stock_record.price_retail = product_sync.price if product_sync.price else 0
                stock_record.num_in_stock = 0
                added_stock_records.append(stock_record)
    update_result = bulk_update(updated_stock_records)
    insert_result = StockRecord.objects.bulk_create(added_stock_records)


def delete_price(product_syncs):
    products = list(map(lambda x: x.product, product_syncs))
    StockRecord.objects.filter(product__in=products).delete()
