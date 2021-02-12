import random as rand
from decimal import *

from django.conf import settings
from oscar.core.loading import get_model

from synchronizer.models import OrderSync
from synchronizer.models import UserSync, ProductSync, VariantSync
from synchronizer.tasks.upload import counter_party
from synchronizer.tasks.upload.static_upload_values import StaticUploadValues
from synchronizer.utils.loader import RequestList

Line = get_model('order', 'Line')
OrderInformation = get_model('shop', 'OrderInformation')

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/customerorder/"


def get_positions(lines, discounts, order):
    positions = []
    for line in lines:

        product_sync = ProductSync.objects.filter(product_id=line.product.id).first()
        sync_type = 'product'
        href_start = 'https://online.moysklad.ru/api/remap/1.1/entity/product/'
        if product_sync is None:
            product_sync = VariantSync.objects.filter(product_id=line.product.id).first()
            sync_type = 'variant'
            href_start = 'https://online.moysklad.ru/api/remap/1.1/entity/variant/'
        price = 0
        discount = 0
        vouchers = [discount for discount in discounts if discount.voucher is not None]
        if len(vouchers) > 0 and vouchers[0].category == 'Basket':
            if vouchers[0].voucher.benefit.type == 'Percentage':
                price = line.unit_price_excl_tax * 100
                discount = discounts[0].voucher.benefit.value
            elif vouchers[0].voucher.benefit.type == 'Absolute':
                price = line.line_price_excl_tax * 100 / line.quantity
                discount = 0

        else:
            price = line.line_price_excl_tax * 100 / line.quantity
            discount = 0
        position = {
            'quantity': line.quantity,
            'price': price,
            'discount': discount,
            'assortment': {
                'meta': {
                    'href': href_start + product_sync.sync_id,
                    'type': sync_type,
                    'mediaType': 'application/json'
                }
            }
        }
        positions.append(position)

    if order.shipping_method in StaticUploadValues.shipping_items.keys():
        position = {
            "quantity": 1,
            "price": Decimal((order.shipping_incl_tax * 100)),
            "discount": 0,
            "vat": 0,
            'assortment': {
                "meta": StaticUploadValues.get_shipping_item(order.shipping_method)
            }
        }
        positions.append(position)

    return positions


def upload(order):
    try:
        order_information = OrderInformation.objects.get(order=order)
    except:
        order_information = None

    description = f'Aдрес доставка: {order.shipping_address};\n' \
                  f'{str(order_information)}\n' \
                  f'Номер телефона: {order.shipping_address.phone_number}\n '

    random_id = rand.randrange(0, 100000)
    user_sync = UserSync.objects.find_by_order(order)
    if user_sync is None:
        user_sync = counter_party.upload(email=order.email if order.email else order.user.email,
                                         name=order.shipping_address.name,
                                         phone=order.shipping_address.phone_number.raw_input,
                                         user=order.user)

    discounts = list(order.discounts.all())
    for discount in discounts:
        description = description + '\nCкидка: \n' + str(discount.offer_name)

    lines = Line.objects.filter(order=order).all()
    data = {'name': settings.MOY_SKLAD_DOC_NAME_PREF + '_' + str(order.number) + '_' + str(
        random_id) + settings.MOY_SKLAD_DOC_NAME_END,
            'agent': StaticUploadValues.get_counter_party_container(str(user_sync.sync_id)),
            'organization': StaticUploadValues.organization_meta_container,
            'attributes': [],  # discount
            'description': description,
            'positions': get_positions(lines, discounts, order)}  # order variants

    result = RequestList.upload(default_url, json_data=data)
    order_sync = OrderSync(order_sync_id=result.get('id'), order=order, counter_party_id=user_sync.sync_id)
    order_sync.save()
    return result


def get_order_meta(sync_id, order_type):
    return {
        'href': 'https://online.moysklad.ru/api/remap/1.1/entity/' + order_type + '/' + sync_id,
        'metadataHref': 'https://online.moysklad.ru/api/remap/1.1/entity/' + order_type + '/metadata',
        'type': order_type,
        'mediaType': 'application/json'
    }


def get_customer_meta(sync_id):
    return get_order_meta(str(sync_id), 'customerorder')


def get_invoice_meta(sync_id):
    return get_order_meta(str(sync_id), 'invoiceout')
