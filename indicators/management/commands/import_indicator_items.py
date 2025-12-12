from django.core.management.base import BaseCommand, CommandError
from indicators.models import Indicator, IndicatorListItem
import os

class Command(BaseCommand):
    help = 'Imports a list of items from a text file (one item per line) into an Indicator.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the text file.')
        parser.add_argument('indicator_id', type=int, help='ID of the parent Indicator.')

    def handle(self, *args, **options):
        file_path = options['file_path']
        indicator_id = options['indicator_id']

        try:
            indicator = Indicator.objects.get(pk=indicator_id)
        except Indicator.DoesNotExist:
            raise CommandError(f'Indicator with ID "{indicator_id}" does not exist.')

        if not os.path.exists(file_path):
            raise CommandError(f'File "{file_path}" does not exist.')

        items_to_create = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name:
                        items_to_create.append(
                            IndicatorListItem(
                                indicator=indicator,
                                name=name,
                                code=''
                            )
                        )
        except Exception as e:
            raise CommandError(f'Error reading file: {e}')

        if items_to_create:
            IndicatorListItem.objects.bulk_create(items_to_create)
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(items_to_create)} items to "{indicator.name}".'))
        else:
            self.stdout.write(self.style.WARNING('No items found in the file.'))
