import csv

from django.core.management.base import BaseCommand
from terms.models import Category, Term, Alias
from django.conf import settings


class Command(BaseCommand):
    help = "network.csvをインポートする"

    def handle(self, *args, **options):
        # プロジェクトルート（manage.pyがある場所）
        csv_path = settings.BASE_DIR / "data" / "network.csv"

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Categoryを取得（なければ作成）
                category, _ = Category.objects.get_or_create(name=row["category"])

                # Termを取得（なければ作成）
                term, created = Term.objects.get_or_create(
                    category=category,
                    word=row["word"],
                    defaults={"description": row["description"]},
                )

                # 既存データの説明を更新したい場合
                if not created and term.description != row["description"]:
                    term.description = row["description"]
                    term.save()

                # Aliasを登録
                aliases = row["aliases"].strip()

                if aliases:
                    for alias in aliases.split("|"):
                        Alias.objects.get_or_create(
                            term=term,
                            alias=alias.strip(),
                        )

                self.stdout.write(self.style.SUCCESS(f"登録完了: {term.word}"))

        self.stdout.write(self.style.SUCCESS("CSVのインポートが完了しました。"))
