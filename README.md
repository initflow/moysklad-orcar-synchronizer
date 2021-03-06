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
    OSCAR_SLUG_FUNCTION = 'synchronizer.utils.slugifier' # for oscar>=2.0.0
    CELERY_APP = 'celery_config.app'
    
    MOYSKLAD_TOKEN = os.environ.get('MOYSKLAD_TOKEN', "")
    MOYSKLAD_MEDIA_URL = os.environ.get("MOYSKLAD_MEDIA_URL", 'images/products/moysklad')
    MOYSKLAD_MEDIA_ROOT = os.path.join(MEDIA_ROOT, MOYSKLAD_MEDIA_URL)
    MOYSKLAD_DOC_NAME_PREF = os.environ.get("MOYSKLAD_DOC_NAME_PREF", "IM")
    MOYSKLAD_DOC_NAME_END = os.environ.get("MOYSKLAD_DOC_NAME_END", "_test")
    MOYSKLAD_USER_LOADED_GROUP = os.environ.get("MOYSKLAD_USER_LOADED_GROUP", "")
```

5. Run migrations ``python manage.py migrate synchronizer``
6. Synchronize ``python manage.py sync_database``

