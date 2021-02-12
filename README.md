# moysklad-orcar-synchronizer

Quick start
-----------

1. Add ``synchronizer`` to your INSTALLED_APPS in settings.py::

```
 INSTALLED_APPS = (
        ...,
        'synchronizer',
        ...,
    )
```

2. Configure django settings

```
    MOYSKLAD_TOKEN = ""
    MOYSKLAD_MEDIA_URL = 'images/products/moysklad'
    MOYSKLAD_MEDIA_ROOT = os.path.join(MEDIA_ROOT, MOYSKLAD_MEDIA_URL)
    MOY_SKLAD_DOC_NAME_PREF = os.environ.get("MOY_SKLAD_DOC_NAME_PREF", "IM")
    MOY_SKLAD_DOC_NAME_END = os.environ.get("MOY_SKLAD_DOC_NAME_END", "_test")
    MOYSKLAD_USER_LOADED_GROUP = 'https://online.moysklad.ru/api/remap/1.1/entity/group/123-456-789'

```
    
3. Run ``python manage.py makemigrations synchronizer && python manage.py migrate synchronizer`` to create models.

