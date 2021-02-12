from datetime import datetime
from synchronizer.models import UserSync
from synchronizer.utils.loader import RequestList

default_url = "https://online.moysklad.ru/api/remap/1.1/entity/counterparty/"


def upload(name, email, phone, user=None):
    attributes = []
    data = {'name': name, 'email': email, 'phone': phone,
            'actualAddress': '', 'attributes': attributes}
    result = RequestList.upload(default_url, json_data=data)

    updated_date = datetime.strptime(result.get('updated'), '%Y-%m-%d %H:%M:%S') if result.get(
        'updated') is not None else None

    user_sync = UserSync(sync_id=result.get('id'), user=user, updated=updated_date,
                         archived=result.get('archived'), email=result.get('email'))
    user_sync.save()
    return user_sync
