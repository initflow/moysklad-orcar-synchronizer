from django.db import models
from oscar.core.loading import get_model


Product = get_model('catalogue', 'Product')
Order = get_model('order', 'Order')


class ProductInformation(models.Model):
    product = models.OneToOneField(Product)
    hide = models.BooleanField(default=False, db_index=True)


class OrderInformation(models.Model):
    order = models.OneToOneField(Order, related_name='order_information')
    comment = models.CharField(null=True, blank=True, max_length=1000)

    def __str__(self):
        return 'Комментарий: {0}'.format(str(self.comment) if self.comment else '') + ';\n'

