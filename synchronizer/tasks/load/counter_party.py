from django.conf import settings
from django.db.models import Q
from oscar.core.compat import get_user_model

from synchronizer.models import UserSync
from synchronizer.utils.loader import RequestList
from synchronizer.utils.util import get_map_objects_by_sync_id, update_or_insert

User = get_user_model()

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/counterparty/"

discount_type_enum = {
    'accumulationdiscount':
        (lambda row, model: setattr(model, 'demand_sum_correction', row.get('demandSumCorrection'))),
    'personaldiscount':
        (lambda row, model: setattr(model, 'personal_discount', row.get('personalDiscount')))
}


def fasdfsd(x, model) -> None:
    model.personal_discount = x.get('personalDiscount')


def execute(last_update=None):
    params = {"filter": 'group=' + settings.MOYSKLAD_USER_LOADED_GROUP}
    if last_update:
        params['updatedFrom'] = last_update.strftime('%Y-%m-%d %H:%M:%S')

    update_pv(RequestList.load_rows_by_url(default_url, params=params))


def update_pv(counter_party_rows):
    changed_user_sync_objs = []
    sync_ids_user_with_emails = list(map(lambda x: x.get('id'), (filter(lambda x: 'email' in x,
                                                                        counter_party_rows))))
    user_sync_db_objs = get_map_objects_by_sync_id(
        UserSync.objects.get_by_sync_ids(sync_ids_user_with_emails)
    )

    for counter_party_row in counter_party_rows:
        sync_id = counter_party_row.get('id')
        user = user_sync_db_objs.get(sync_id)
        if not user and ('email' in counter_party_row):
            user = UserSync(sync_id=sync_id)
            email = counter_party_row['email']
            try:
                customer = User.objects.get(Q(username=email) or Q(email=email))
            except:
                customer = User.objects.create_user(email, email)
            user.user = customer

        if user:
            discount_rows = counter_party_row.get('discounts')
            if discount_rows:
                for discount_row in discount_rows:
                    if discount_row.get('discount') and discount_row.get('discount').get('meta').get('type'):
                        discount_type = str(discount_row.get('discount').get('meta').get('type'))
                        discount_type_enum.get(discount_type)(discount_row, user)

            changed_user_sync_objs.append(user)

    update_or_insert(changed_user_sync_objs, UserSync.objects)
