import random as rand
import logging
from synchronizer.helpers import generate_sync_id
from synchronizer.models import OrderSync
from synchronizer.tasks.upload.customer_order import get_customer_meta
from synchronizer.utils.loader import RequestList
from synchronizer.tasks.upload.static_upload_values import StaticUploadValues
from django.conf import settings

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/paymentin/"


def upload(order):
    logging.info("Sending PaymentIn")
    random_id = rand.randrange(0, 100000)
    order_sync = OrderSync.objects.filter(order=order).first()
    if order_sync is not None:
        customer_order_meta = get_customer_meta(order_sync.order_sync_id)

        operations = {
            'meta': customer_order_meta,
            'linkedSum': order.total_incl_tax * 100
        }

        sync_id = generate_sync_id(str(order.number))

        data = {
            'syncId': sync_id,
            'name': '{}_{}_{}_{}'.format(
                settings.MOYSKLAD_DOC_NAME_PREF,
                str(order.id),
                str(random_id),
                settings.MOYSKLAD_DOC_NAME_END),
            'agent': StaticUploadValues.get_counter_party_container(str(order_sync.counter_party_id)),
            'organization': StaticUploadValues.organization_meta_container,
            'sum': order.total_incl_tax * 100,
            'operations': [operations]
        }
        result = RequestList.upload(default_url, json_data=data)

        order_sync.payment_sync_id = result.get('id')
        order_sync.save()
        return result
