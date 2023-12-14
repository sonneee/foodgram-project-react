import csv
import os

from foodgram import settings

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag


def create_ingridient(text):
    Ingredient.objects.get_or_create(
        name=text[0],
        measurement_unit=text[1]
    )


def create_tag(text):
    Tag.objects.get_or_create(
        name=text[0],
        color=text[1],
        slug=text[2]
    )


class Command(BaseCommand):
    help = 'Load ingredients.csv to db'

    def handle(self, *args, **options):
        path_ingr = os.path.join(settings.BASE_DIR, 'ingredients.csv')
        path_tags = os.path.join(settings.BASE_DIR, 'tags.csv')
        try:
            table = open(path_ingr, 'r', encoding='utf-8')
        except FileNotFoundError:
            self.stdout.write(
                self.style.WARNING('No file ingredients.csv provided'))
        else:
            with table:
                counter = 0
                reader = csv.reader(table)
                for row in reader:
                    create_ingridient(row)
                    counter += 1
            self.stdout.write(
                self.style.SUCCESS('%s ingridients loaded to db' % counter)
            )
        try:
            table = open(path_tags, 'r', encoding='utf-8')
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING('No file tags.csv provided'))
        else:
            with table:
                counter = 0
                reader = csv.reader(table)
                for row in reader:
                    create_tag(row)
                    counter += 1
            self.stdout.write(
                self.style.SUCCESS('%s tags loaded to db' % counter)
            )
