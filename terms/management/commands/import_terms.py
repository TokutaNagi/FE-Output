import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from terms.models import Alias, Category, Term


class Command(BaseCommand):
    help = "CSVをインポートする"

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str)

    def handle(self, *args, **options):
        csv_path = settings.BASE_DIR / "data" / options["filename"]

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                category, _ = Category.objects.get_or_create(name=row["category"])

                term, created = Term.objects.get_or_create(
                    category=category,
                    word=row["word"],
                    defaults={
                        "description": row["description"],
                    },
                )

                if not created and term.description != row["description"]:
                    term.description = row["description"]
                    term.save()

                aliases = row["aliases"].strip()

                if aliases:
                    for alias in aliases.split("|"):
                        Alias.objects.get_or_create(
                            term=term,
                            alias=alias.strip(),
                        )

                self.stdout.write(self.style.SUCCESS(f"登録完了: {term.word}"))

        self.stdout.write(self.style.SUCCESS("CSVのインポートが完了しました。"))
