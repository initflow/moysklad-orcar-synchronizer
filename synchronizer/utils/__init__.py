from unidecode import unidecode
from django.utils import six
from django.utils.text import slugify as django_slugify


def slugifier(value, allow_unicode=False):
    if not allow_unicode:
        value = unidecode(six.text_type(value))

    return django_slugify(value, allow_unicode=allow_unicode)
