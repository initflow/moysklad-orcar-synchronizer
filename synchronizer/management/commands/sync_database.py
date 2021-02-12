from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-f", "--force-update", default=False, action='store_true',
                            help="Force download and update all objects")
        parser.add_argument('--delete', action='store_true', default=False)

    def handle(self, *args, **kwargs):
        print('Initialize moysklad')
        from synchronizer.tasks import initial_task

        force_update: bool = kwargs.get("force_update", False)
        is_delete: bool = kwargs.get("delete", False)

        initial_task(force_full_update=force_update, is_delete=is_delete)
