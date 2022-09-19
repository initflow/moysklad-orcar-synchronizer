from django.conf import settings

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.apps.catalogue.models import Category

from synchronizer.models import ProductFolderSync
from synchronizer.utils.loader import RequestList
from synchronizer.utils.optional import Optional
from synchronizer.utils.util import get_map_objects_by_id_element_row, parse_date_for_moscow, only_insert_and_return_all


default_url = "https://online.moysklad.ru/api/remap/1.1/entity/productfolder/"


def execute(last_update=None):
    folders_rows = []
    params = {}

    if last_update:
        params['updatedFrom'] = last_update.strftime('%Y-%m-%d %H:%M:%S')

    folders_rows.extend(RequestList.load_rows_by_url(default_url, params=params))
    update_pf(folders_rows)


def update_pf(product_folder_rows):
    product_folders_objs = []

    pf_by_sync_id_dict = get_map_objects_by_id_element_row(
        product_folder_rows,
        lambda sync_ids: ProductFolderSync.objects.get_by_sync_ids(sync_ids))

    for row in product_folder_rows:
        if row.get('description') == 'hide':
            continue  # hiding categories
        sync_id = row.get('id')
        pf_from_db = pf_by_sync_id_dict.get(sync_id) if pf_by_sync_id_dict.get(sync_id) else ProductFolderSync()

        parent_id = Optional(row.get('productFolder')).map(lambda x: x.get('meta')) \
            .map(lambda x: x.get('href')).if_exists(lambda x: x.replace(default_url, ''))

        updated_date = parse_date_for_moscow(row.get('updated'))

        pf_from_db.sync_id = sync_id
        pf_from_db.parent_sync_id = parent_id
        pf_from_db.name = row.get('name')
        pf_from_db.path_name = row.get('pathName')
        pf_from_db.archived = row.get('archived')
        pf_from_db.updated = updated_date
        pf_from_db.path_name_changed = None

        product_folders_objs.append(pf_from_db)

    result = only_insert_and_return_all(product_folders_objs, ProductFolderSync.objects)

    dict_by_id = {result[i].sync_id: result[i] for i in range(0, len(result), )}

    for pf in result:
        parent = dict_by_id.get(pf.parent_sync_id)
        pf.parent_product_folder_sync = parent

    for pf in result:
        pf.path_name_changed = change_path(pf)

    ProductFolderSync.objects.bulk_update(result)

    update_categories(result)


def update_categories(product_folder_syncs):
    for pf_sync in product_folder_syncs:
        category = pf_sync.category if pf_sync.category else create_from_breadcrumbs(pf_sync.path_name_changed, '${/}')

        # rename
        if category.name != pf_sync.name:
            category.name = pf_sync.name
            category.slug = category.generate_slug()

        # archived
        category.archived = pf_sync.archived
        category.save()

        if pf_sync.category is None:
            pf_sync.category = category
            pf_sync.save()

        # move
        ancestors = list(category.get_ancestors())
        old_path = ancestors[-1].full_name.replace(' > ', '/') if ancestors else ''
        if pf_sync.path_name != old_path:
            if pf_sync.path_name == '':
                root = Category.objects.filter(depth=1).first()
                if root:
                    category.move(root)
                else:
                    print('Can`t find root category')
            else:
                parent_category = pf_sync.parent_product_folder_sync.category
                category.move(parent_category, 'last-child')

    # delete
    for category in ProductFolderSync.objects.all():
        if category not in product_folder_syncs:
            try:
                category.category.delete()
            except AttributeError:
                pass
            category.delete()

    ProductFolderSync.objects.bulk_update(product_folder_syncs)


def change_path(pf: ProductFolderSync):
    if pf.path_name_changed:
        return pf.path_name_changed
    parent_path = Optional(pf.parent_product_folder_sync) \
        .if_exists(lambda x: x.path_name_changed if x.path_name_changed else change_path(x))
    return parent_path + "${/}" + pf.name if parent_path else pf.name
