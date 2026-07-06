from django.contrib import admin
from .models import Category, Term, Alias

admin.site.register(Category)
admin.site.register(Term)
admin.site.register(Alias)
