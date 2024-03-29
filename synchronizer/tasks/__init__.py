from django.utils.timezone import now
from django.dispatch import receiver
from django.conf import settings
from django.utils.module_loading import import_string
from django.db.models.signals import post_save
from oscar.core.loading import get_model
from oscarapicheckout.signals import order_placed

from synchronizer.models import SyncTaskObject, OrderSync
from .load import accumulation_discount, product_folder, counter_party, delete, product, stock, store, variant
from .upload import invoice_out, payment_in, customer_order

if hasattr(settings, 'MOYSKLAD_TASK_NOTIFIER'):
    import importlib
    notifier = importlib.import_module(settings.MOYSKLAD_TASK_NOTIFIER)
    task_timer = notifier.task_timer
else:
    def task_timer(func):
        def wrap(*args, **kwargs):
            return func(*args, **kwargs)
        return wrap


app = import_string(settings.CELERY_APP)
Order = get_model('order', 'Order')
PaymentEvent = get_model('order', 'PaymentEvent')


@app.task(name="initial_task")
@task_timer
def initial_task(force_full_update: bool = False, is_delete=False):
    if getattr(settings, 'MOYSKLAD_PRODUCT_LOAD', True):
        print('-----PRODUCT UPDATE--------')
        product_update(force_full_update, is_delete)
    if getattr(settings, 'MOYSKLAD_DISCOUNT_LOAD', True):
        print('-----DISCOUNT SYNC--------')
        discount_update(force_full_update)
    if getattr(settings, 'MOYSKLAD_STOCK_LOAD', True):
        print('-----PRODUCT STOCK--------')
        product_sync_stock(force_full_update)


@app.task(name="product_update_task")
@task_timer
def product_update_task(force_full_update: bool = False):
    product_update()


@app.task(name="product_sync_stock_task")
@task_timer
def product_sync_stock_task(force_full_update: bool = False):
    product_sync_stock()


@app.task(name="discount_update_task")
def discount_update_task(force_full_update: bool = False):
    discount_update()


def product_sync_stock(force_full_update: bool = False):
    stock.execute()


def product_update(force_full_update: bool = False, is_delete=False):
    print('-Start product update task-')
    task, created = SyncTaskObject.objects.get_or_create(name='product_update_task')
    last_date = task.last_run_date if not force_full_update else None

    product_folder.execute()
    delete.execute(is_delete)
    store.execute(last_date)
    product.execute(last_date)
    variant.execute(last_date)

    task.last_run_date = now()
    task.save()


def discount_update(force_full_update: bool = False):
    print('-Start discount_update_task-')
    task, created = SyncTaskObject.objects.get_or_create(name='discount_update_task')
    last_date = task.last_run_date if not force_full_update else None

    counter_party.execute(last_date)
    accumulation_discount.execute(last_date)

    task.last_run_date = now()
    task.save()


@receiver(order_placed)
def receive_order_placed(sender, order, user, **kwargs):
    order_sync = OrderSync.objects.filter(order=order).first()
    if order_sync is None:
        co = customer_order.upload(order=order)
        invoice_out.upload(order=order, customer_order_response=co)


@receiver(post_save, sender=Order)
def send_order_to_sklad(sender, instance=None, created=None, update_fields=None, **kwargs):
    order_sync = OrderSync.objects.filter(order=instance).first()
    if not order_sync:
        return

    if order_sync.status != instance.status:
        order_sync.status = instance.status
        order_sync.save()


@receiver(post_save, sender=PaymentEvent)
def upload_payment_in(sender, instance=None, created=None, update_fields=None, **kwargs):
    order = instance.order
    order_sync = OrderSync.objects.filter(order=order).first()
    if order_sync.payment_sync_id is None and 'authori' in instance.event_type.code:
        payment_in.upload(order=order)
