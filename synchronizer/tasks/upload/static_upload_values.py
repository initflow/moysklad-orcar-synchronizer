class StaticUploadValues:

    organization_meta_container = {
        "meta": {

        }
    }

    shipping_items = {

    }

    @staticmethod
    def get_shipping_item(shipping_name):
        shipping_item = StaticUploadValues.shipping_items.get(shipping_name)
        return {
            "href": shipping_item.get('href'),
            "metadataHref": "https://online.moysklad.ru/api/remap/1.1/entity/service/metadata",
            "type": "service",
            "mediaType": "application/json",
            "uuidHref": shipping_item.get('uuidHref')
        }

    @staticmethod
    def get_store_container(sync_id):
        return {
            "meta": {
                "href": "https://online.moysklad.ru/api/remap/1.1/entity/organization/" + sync_id,
                "metadataHref": "https://online.moysklad.ru/api/remap/1.1/entity/organization/metadata",
                "type": "organization",
                "mediaType": "application/json"
            }
        }

    @staticmethod
    def get_counter_party_container(sync_id):
        return {
            "meta": {
                "href": "https://online.moysklad.ru/api/remap/1.1/entity/counterparty/" + sync_id,
                "metadataHref": "https://online.moysklad.ru/api/remap/1.1/entity/counterparty/metadata",
                "type": "counterparty",
                "mediaType": "application/json"
            }
        }
