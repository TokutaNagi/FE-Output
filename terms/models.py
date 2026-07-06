from django.db import models


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
