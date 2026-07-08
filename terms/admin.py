from django.contrib import admin

from .models import (
    Alias,
    Category,
    Result,
    ResultDetail,
    Term,
    UserTermStat,
)

admin.site.register(Category)
admin.site.register(Term)
admin.site.register(Alias)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "question_count",
        "correct_count",
        "incorrect_count",
        "accuracy",
    )
    ordering = ("-created_at",)


@admin.register(ResultDetail)
class ResultDetailAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "result_id",
        "result",
        "term",
        "is_correct",
        "hint_count",
    )

    @admin.display(description="Result ID")
    def result_id(self, obj):
        return obj.result.id


@admin.register(UserTermStat)
class UserTermStatAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "term",
        "mistake_count",
    )

    ordering = ("-mistake_count",)
