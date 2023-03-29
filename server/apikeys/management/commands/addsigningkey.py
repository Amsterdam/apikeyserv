from django.core.management.base import BaseCommand, CommandError

from apikeys.models import SigningKey


class Command(BaseCommand):
    """manage.py addsigningkey"""

    help = "Add a signing key"

    def add_arguments(self, parser):
        parser.add_argument("pemfile", nargs=1, type=str,
                            help="private key file, in PEM format")

    def handle(self, *args, **options):
        with open(options["pemfile"][0]) as f:
            key = SigningKey(private=f.read())
            key.save()
