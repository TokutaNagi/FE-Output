from django.test import TestCase
from terms.models import Category, Term, Alias
from terms.utils import normalize, make_hint, is_correct_answer


class NormalizeTest(TestCase):
    def test_none(self):
        self.assertEqual(normalize(None), "")

    def test_empty(self):
        self.assertEqual(normalize(""), "")

    def test_strip_spaces(self):
        self.assertEqual(normalize("  TCP  "), "tcp")

    def test_uppercase(self):
        self.assertEqual(normalize("TCP"), "tcp")

    def test_full_width(self):
        self.assertEqual(normalize("ＴＣＰ"), "tcp")

    def test_remove_space(self):
        self.assertEqual(normalize("T C P"), "tcp")

    def test_remove_hyphen(self):
        self.assertEqual(normalize("T-C-P"), "tcp")

    def test_remove_slash(self):
        self.assertEqual(normalize("T/C/P"), "tcp")

    def test_remove_underscore(self):
        self.assertEqual(normalize("T_C_P"), "tcp")

    def test_remove_middle_dot(self):
        self.assertEqual(normalize("T・C・P"), "tcp")

    def test_mixed(self):
        self.assertEqual(
            normalize("  Ｔ-Ｃ／Ｐ・ "),
            "tcp",
        )


class MakeHintTest(TestCase):
    def test_hint_count_zero(self):
        self.assertEqual(make_hint("python", 0), "______")

    def test_hint_count_one(self):
        self.assertEqual(make_hint("python", 1), "p_____")

    def test_hint_count_middle(self):
        self.assertEqual(make_hint("python", 3), "pyt___")

    def test_hint_count_all(self):
        self.assertEqual(make_hint("python", 6), "python")

    def test_hint_count_over_length(self):
        self.assertEqual(make_hint("python", 10), "python")

    def test_empty_word(self):
        self.assertEqual(make_hint("", 0), "")


class IsCorrectAnswerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="ネットワーク")

        self.term = Term.objects.create(
            category=self.category,
            word="TCP",
            description="説明",
        )

        Alias.objects.create(
            term=self.term,
            alias="Transmission Control Protocol",
        )

    def test_correct_word(self):
        self.assertTrue(is_correct_answer(self.term, "TCP"))

    def test_alias(self):
        self.assertTrue(
            is_correct_answer(
                self.term,
                "Transmission Control Protocol",
            )
        )

    def test_wrong_answer(self):
        self.assertFalse(
            is_correct_answer(
                self.term,
                "UDP",
            )
        )

    def test_uppercase(self):
        self.assertTrue(is_correct_answer(self.term, "tcp"))

    def test_fullwidth(self):
        self.assertTrue(is_correct_answer(self.term, "ＴＣＰ"))
