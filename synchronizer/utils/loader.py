import requests
from django.conf import settings


class RequestList:

    @staticmethod
    def load_one_row_by_url(uri, params=None):
        return RequestList.__load(uri, 1, 1, update_from=None, params=params)

    @staticmethod
    def load_rows_by_url(uri, limit=100, updated_from=None, params=None):
        result = []
        offset = 0
        while offset < 10000:
            rows = RequestList.__load(uri, limit, offset, updated_from, params)['rows']
            if not rows:
                break
            result.extend(rows)
            offset += limit
        return result

    @staticmethod
    def __load(uri, limit, offset, update_from=None, params=None):
        payload = {'limit': limit, 'offset': offset, 'archived': 'All'}
        if update_from:
            payload['update_from'] = update_from
        if params:
            payload.update(params)
        headers = {'Content-Type': 'application/json', 'Authorization': 'Basic ' + settings.MOYSKLAD_TOKEN}
        return requests.get(uri, params=payload, headers=headers).json()

    @staticmethod
    def upload(url, json_data):
        headers = {'Content-Type': 'application/json', 'Authorization': 'Basic ' + settings.MOYSKLAD_TOKEN}
        return requests.post(url, json=json_data, headers=headers).json()
