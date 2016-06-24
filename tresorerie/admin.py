from django.contrib import admin

from .models import MonthlyPayment, Transaction

admin.site.register(MonthlyPayment)
admin.site.register(Transaction)