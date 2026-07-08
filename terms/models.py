from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Term(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="terms"
    )
    word = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.word


class Alias(models.Model):
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="aliases")
    alias = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.alias


class Result(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="results",
        null=True,
        blank=True,
    )
    categories = models.ManyToManyField(
        Category,
        related_name="results",
        verbose_name="カテゴリ",
    )
    question_count = models.PositiveIntegerField()
    correct_count = models.PositiveIntegerField()
    incorrect_count = models.PositiveIntegerField()
    accuracy = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "リザルト"
        verbose_name_plural = "リザルト"

    def __str__(self):
        username = self.user.username if self.user else "ゲスト"

        return (
            f"{username} "
            f"{self.created_at:%Y/%m/%d %H:%M} "
            f"({self.correct_count}/{self.question_count})"
        )


class ResultDetail(models.Model):
    result = models.ForeignKey(
        Result,
        on_delete=models.CASCADE,
        related_name="details",
    )
    term = models.ForeignKey(
        "Term",
        on_delete=models.CASCADE,
    )
    is_correct = models.BooleanField()
    hint_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["id"]
        verbose_name = "リザルト詳細"
        verbose_name_plural = "リザルト詳細"

    def __str__(self):
        return self.term.word


class UserTermStat(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="term_stats",
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="user_stats",
    )
    mistake_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "ユーザー用語統計"
        verbose_name_plural = "ユーザー用語統計"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "term"],
                name="unique_user_term",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.term.word} ({self.mistake_count})"
