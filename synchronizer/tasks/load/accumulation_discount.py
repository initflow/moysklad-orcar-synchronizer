from synchronizer.models import AccumulationDiscountSync
from synchronizer.utils.loader import RequestList
from synchronizer.utils.util import get_map_objects_by_id_element_row, update_or_insert


default_url = 'https://online.moysklad.ru/api/remap/1.1/entity/accumulationdiscount/'


def execute(last_update=None):
    params = {}
    if last_update:
        params['updatedFrom'] = last_update.strftime('%Y-%m-%d %H:%M:%S')
    update_discount(RequestList.load_rows_by_url(default_url, params=params))


def update_discount(discounts_rows):
    discounts = []
    sync_id_db_obj_map = get_map_objects_by_id_element_row(
        discounts_rows,
        lambda sync_ids: AccumulationDiscountSync.objects.get_by_sync_ids(sync_ids))

    for discount_row in discounts_rows:
        sync_id = discount_row.get('id')
        discount = sync_id_db_obj_map.get(sync_id)
        discount = AccumulationDiscountSync() if discount is None else discount

        discount.sync_id = sync_id
        discount.name = discount_row.get('name')
        discount.active = discount_row.get('active')
        discount.set_levels(discount_row.get('levels'))

        discounts.append(discount)

    update_or_insert(discounts, AccumulationDiscountSync.objects)
