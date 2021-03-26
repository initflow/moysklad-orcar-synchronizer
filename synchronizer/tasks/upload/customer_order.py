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
Product = get_model('catalogue', 'Product')
OrderInformation = get_model('shop', 'OrderInformation')

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/customerorder/"


class AbstractPosition:
    def __init__(self, quantity: int, price: Decimal, discount: float, sync_id: str, sync_type: str):
        self.quantity = quantity
        self.price = price * 100
        self.discount = discount
        self.sync_id = sync_id
        self.sync_type = sync_type

    @property
    def data(self) -> dict:
        return {
            'quantity': self.quantity,
            'price': self.price * 100,
            'discount': self.discount,
            'assortment': {
                'meta': {
                    'href': f'https://online.moysklad.ru/api/remap/1.1/entity/{self.sync_type}/{self.sync_id}',
                    'type': self.sync_type,
                    'mediaType': 'application/json'
                }
            }
        }


class ProductPosition(AbstractPosition):
    def __init__(self, quantity: int, price: Decimal, discount: float, product: Product):
        product_sync = ProductSync.objects.filter(product_id=product.id).first()
        if product_sync:
            sync_type = 'product'
        else:
            product_sync = VariantSync.objects.filter(product_id=product.id).first()
            sync_type = 'variant'
        super().__init__(quantity, price, discount, product_sync.sync_id, sync_type)


class ServicePosition(AbstractPosition):
    def __init__(self, quantity: int, price: Decimal, discount: float, sync_id: str):
        sync_type = 'service'
        super().__init__(quantity, price, discount, sync_id, sync_type)


def get_positions(lines, discounts, order):
    positions = []
    for line in lines:
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

        position = ProductPosition(
            quantity=line.quantity,
            price=price,
            discount=discount,
            product=line.product)
        positions.append(position)

    # if order.shipping_incl_tax > 0:
    #     position = ServicePosition(
    #         quantity=1,
    #         price=order.shipping_incl_tax,
    #         discount=0,
    #         sync_id='1054042d-6a24-11e7-7a69-97110006dc67')
    #     positions.append(position)
    return positions


def get_description(order):
    order_information = OrderInformation.objects.first(order=order)
    description = f'Aдрес доставка: {order.shipping_address};\n' \
                  f'{str(order_information)}\n' \
                  f'Номер телефона: {order.shipping_address.phone_number}\n '

    discounts = list(order.discounts.all())
    for discount in discounts:
        description = description + '\nCкидка: \n' + str(discount.offer_name)

    return description


def upload(order):
    user_sync = UserSync.objects.find_by_order(order)
    if user_sync is None:
        user_sync = counter_party.upload(
            email=order.email if order.email else order.user.email,
            name=order.shipping_address.name,
            phone=order.shipping_address.phone_number.raw_input,
            user=order.user)

    lines = Line.objects.filter(order=order).all()
    description = get_description(order)
    discounts = list(order.discounts.all())
    random_id = rand.randrange(0, 100000)
    positions = [position.data for position in get_positions(lines, discounts, order)]

    data = {'name': settings.MOY_SKLAD_DOC_NAME_PREF + '_' + str(order.number) + '_' + str(
        random_id) + settings.MOY_SKLAD_DOC_NAME_END,
            'agent': StaticUploadValues.get_counter_party_container(str(user_sync.sync_id)),
            'organization': StaticUploadValues.organization_meta_container,
            'attributes': [],
            'description': description,
            'positions': positions}

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
