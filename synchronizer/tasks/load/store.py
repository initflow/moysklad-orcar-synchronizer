from oscar.apps.address.models import Country
from oscar.apps.partner.models import Partner, PartnerAddress
from synchronizer.models import StoreSync
from synchronizer.utils.loader import RequestList
from synchronizer.utils.util import get_map_objects_by_id_element_row, parse_date_for_moscow, update_or_insert


default_url = "https://online.moysklad.ru/api/remap/1.1/entity/store/"


def execute(last_update=None):
    load_filter = ''
    params = {"filter": load_filter}
    if last_update:
        params['updatedFrom'] = last_update.strftime('%Y-%m-%d %H:%M:%S')

    rows = RequestList.load_rows_by_url(default_url, params=params)
    update_pv(rows)


def update_pv(store_rows):
    store_objs = []
    store_db_by_sync_id_dict = get_map_objects_by_id_element_row(
        store_rows, lambda sync_ids: StoreSync.objects.get_by_sync_ids(sync_ids))

    for row in store_rows:
        sync_id = row.get('id')
        store_from_db_or_new = store_db_by_sync_id_dict.get(sync_id) if store_db_by_sync_id_dict.get(
            sync_id) else StoreSync()

        updated_date = parse_date_for_moscow(row.get('updated'))

        store_from_db_or_new.sync_id = sync_id
        store_from_db_or_new.updated = updated_date
        store_from_db_or_new.name = row.get('name')
        store_from_db_or_new.archived = row.get('archived')
        store_from_db_or_new.path_name = row.get('pathName')
        store_from_db_or_new.address = row.get('address')
        store_from_db_or_new.description = row.get('description')

        store_objs.append(store_from_db_or_new)

    result = update_or_insert(store_objs, StoreSync.objects)
    update_store(result)


def update_store(store_syncs):
    country, created = Country.objects.get_or_create(
        iso_3166_1_a2='RU', defaults={'name': 'Россия', 'printable_name': 'Россия'})

    for store_sync in store_syncs:
        partner = store_sync.partner if store_sync.partner \
            else Partner.objects.filter(code=store_sync.name).first()
        partner = partner if partner else Partner()
        partner.name = store_sync.name
        partner.code = store_sync.name
        partner.save()

        partner = partner if partner.id else Partner.objects.filter(code=store_sync.name, name=store_sync.name).first()
        store_sync.partner = partner

        store_addr = PartnerAddress.objects.filter(partner=partner).first()
        store_addr = store_addr if store_addr else PartnerAddress()

        store_addr.partner = partner
        store_addr.title = store_sync.name
        store_addr.line1 = store_sync.address if store_sync.address else 'Адресс не указан;'
        store_addr.line4 = store_sync.description if store_sync.description else 'Город не указан;'
        store_addr.country = country
        store_addr.save()

    StoreSync.objects.bulk_update(store_syncs)
