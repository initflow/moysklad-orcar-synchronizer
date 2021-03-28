# moysklad-orcar-synchronizer

Quick start
-----------
1. Install  ``git+https://github.com/initflow/moysklad-orcar-synchronizer`` 

2. Add ``synchronizer`` to your INSTALLED_APPS in settings.py

```
 INSTALLED_APPS = (
        ...,
        'synchronizer',
        ...,
    )
```

3. Get api token. Encode base64 ``login:password``

4. Configure django settings

```
    MOYSKLAD_TOKEN = ""
    MOYSKLAD_MEDIA_URL = 'images/products/moysklad'
    MOYSKLAD_MEDIA_ROOT = os.path.join(MEDIA_ROOT, MOYSKLAD_MEDIA_URL)
    MOY_SKLAD_DOC_NAME_PREF = os.environ.get("MOY_SKLAD_DOC_NAME_PREF", "IM")
    MOY_SKLAD_DOC_NAME_END = os.environ.get("MOY_SKLAD_DOC_NAME_END", "_test")
    MOYSKLAD_USER_LOADED_GROUP = 'https://online.moysklad.ru/api/remap/1.1/entity/group/123-456-789'

```

5. Run migrations ``python manage.py migrate synchronizer``
6. Synchronize ``python manage.py sync_database``

