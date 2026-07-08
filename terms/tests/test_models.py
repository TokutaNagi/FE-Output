from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from terms.models import (
    Alias,
    Category,
    Result,
    ResultDetail,
    Term,
    UserTermStat,
)


class ModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nagi",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(
            name="ネットワーク",
        )

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

        self.alias = Alias.objects.create(
            term=self.term,
            alias="ティーシーピー",
        )

        self.result = Result.objects.create(
            user=self.user,
            question_count=10,
            correct_count=8,
            incorrect_count=2,
            accuracy=80,
        )

        self.result.categories.add(self.category)

        self.detail = ResultDetail.objects.create(
            result=self.result,
            term=self.term,
            is_correct=True,
            hint_count=0,
        )

        self.stat = UserTermStat.objects.create(
            user=self.user,
            term=self.term,
            mistake_count=3,
        )

    def test_category_str(self):
        self.assertEqual(
            str(self.category),
            "ネットワーク",
        )

    def test_term_str(self):
        self.assertEqual(
            str(self.term),
            "TCP",
        )

    def test_alias_str(self):
        self.assertEqual(
            str(self.alias),
            "ティーシーピー",
        )

    def test_result_str(self):
        result = str(self.result)

        self.assertIn(
            "nagi",
            result,
        )

        self.assertIn(
            "(8/10)",
            result,
        )

    def test_result_detail_str(self):
        self.assertEqual(
            str(self.detail),
            "TCP",
        )

    def test_user_term_stat_str(self):
        self.assertEqual(
            str(self.stat),
            "nagi - TCP (3)",
        )

    def test_user_term_unique(self):
        # エラーが出たら成功
        with self.assertRaises(IntegrityError):
            UserTermStat.objects.create(
                user=self.user,
                term=self.term,
                mistake_count=1,
            )
