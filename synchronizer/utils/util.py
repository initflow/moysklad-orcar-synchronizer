from datetime import datetime
from pytz import timezone


def check_id_is_none_and_add_to_list(obj, list_with_id, list_without_id):
    if obj.id is None:
        list_without_id.append(obj)
    else:
        list_with_id.append(obj)


def update_or_insert(elements, update_manager):
    insertable = list(filter(lambda x: x.id is None, elements))
    updatable = list(filter(lambda x: x.id is not None, elements))

    result = update_manager.bulk_create(insertable)
    update_manager.bulk_update(updatable)
    result.extend(updatable)

    return result


def only_insert_and_return_all(elements, update_manager):
    insertable = list(filter(lambda x: x.id is None, elements))
    updatable = list(filter(lambda x: x.id is not None, elements))

    result = update_manager.bulk_create(insertable)
    result.extend(updatable)

    return result


def get_map_objects_by_id_element_row(rows_with_id, loader_obj_with_sync_id_func):
    sync_ids = list(map(lambda x: x.get('id'), rows_with_id))
    database_obj = loader_obj_with_sync_id_func(sync_ids)

    obj_in_dict = {}
    for obj in database_obj:
        obj_in_dict[obj.sync_id] = obj
    return obj_in_dict


def get_map_objects_by_sync_id(database_obj):
    obj_in_dict = {}
    for obj in database_obj:
        obj_in_dict[obj.sync_id] = obj
    return obj_in_dict


def parse_date_for_moscow(date_str):
    updated_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') if date_str is not None else None
    return timezone('Europe/Moscow').localize(updated_date)
