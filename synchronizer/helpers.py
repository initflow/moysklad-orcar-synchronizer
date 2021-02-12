import uuid


def product_title_parser_fun(name):
    return name


product_title_parser = product_title_parser_fun


def generate_sync_id(uniq_name=None):
    if uniq_name is None:
        return str(uuid.uuid4())
    return str(uuid.uuid5(uuid.NAMESPACE_OID, uniq_name))
