import csv
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag
from foodgram import settings


def create_ingridient(name, measure):
    Ingredient.objects.get_or_create(
        name=name,
        measurement_unit=measure
    )


def create_tag(name, color, slug):
    Tag.objects.get_or_create(
        name=name,
        color=color,
        slug=slug
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
                for name, measure in reader:
                    create_ingridient(name, measure)
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
                for name, color, slug in reader:
                    create_tag(name, color, slug)
                    counter += 1
            self.stdout.write(
                self.style.SUCCESS('%s tags loaded to db' % counter)
            )
