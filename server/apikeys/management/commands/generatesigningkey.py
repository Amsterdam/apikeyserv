from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from django.core.management.base import BaseCommand

from apikeys import pqc
from apikeys.models import ALGORITHM_EDDSA, SigningKey


class Command(BaseCommand):
    """manage.py generatesigningkey [--algorithm eddsa|ml-dsa-65]

    Generates a new signing key pair directly and stores it as a SigningKey, rather
    than requiring an external tool's output to be piped through addsigningkey.
    Needed for ML-DSA-65 in particular, since `openssl genpkey` can't produce one.
    """

    help = "Generate a new signing key pair and add it as a SigningKey"

    def add_arguments(self, parser):
        parser.add_argument(
            "--algorithm",
            choices=["eddsa", "ml-dsa-65"],
            default="eddsa",
            help="The key algorithm to generate (default: eddsa)",
        )

    def handle(self, *args, **options):
        if options["algorithm"] == "ml-dsa-65":
            private_pem = pqc.generate_private_key_pem()
            algorithm = pqc.ALGORITHM
        else:
            private_key = Ed25519PrivateKey.generate()
            private_pem = private_key.private_bytes(
                Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
            ).decode("ascii")
            algorithm = ALGORITHM_EDDSA

        key = SigningKey(private=private_pem, algorithm=algorithm)
        key.save()
        self.stdout.write(self.style.SUCCESS(f"Created SigningKey id={key.id} algorithm={algorithm}"))
