from oscar.apps.catalogue.models import Product
from oscar.core.loading import get_model

from synchronizer.models import VariantSync, ProductSync
from synchronizer.utils.loader import RequestList

ProductInformation = get_model('shop', 'ProductInformation')

default_product_url = "https://online.moysklad.ru/api/remap/1.1/entity/product/"
default_variant_url = "https://online.moysklad.ru/api/remap/1.1/entity/variant/"


def execute(is_delete=False):
    if not is_delete:
        return
    products_rows = RequestList.load_rows_by_url(default_product_url) \
                    + RequestList.load_rows_by_url(default_variant_url)
    delete_product(products_rows)


def delete_product(product_rows):
    products = Product.objects.all()
    new_products = set(product['id'] for product in product_rows if not product['archived'])
    for product in products:
        hide = True
        if VariantSync.objects.filter(product=product).exists():
            hide = VariantSync.objects.get(product=product).sync_id not in new_products
        elif ProductSync.objects.filter(product=product).exists():
            hide = ProductSync.objects.get(product=product).sync_id not in new_products
        ProductInformation.objects.update_or_create(
            product=product, defaults={'hide': hide})
