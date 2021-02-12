from oscar.apps.order.models import Line
from synchronizer.models import OrderSync
from synchronizer.utils.loader import RequestList
from synchronizer.tasks.upload.customer_order import get_positions

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/invoiceout/"


def upload(order, customer_order_response):
    discounts = list(order.discounts.all())
    positions = get_positions(Line.objects.filter(order=order).all(), discounts, order)
    data = {'name': customer_order_response['name'],
            'agent': customer_order_response.get('agent'),
            'organization': customer_order_response.get('organization'),
            'store': customer_order_response.get('store'),
            'attributes': [],  # discount
            'description': customer_order_response.get('description'),
            'customerOrder': {
                'meta': customer_order_response.get('meta')
                },
            'positions': positions}  # order variants

    result = RequestList.upload(default_url, json_data=data)

    order_sync = OrderSync.objects.filter(order=order).first()
    order_sync.invoice_out_sync_id = result.get('id')
    order_sync.save()
    return result
