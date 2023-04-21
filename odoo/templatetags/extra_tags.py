from datetime import datetime

from django import template

register = template.Library()


@register.filter
def receipt_type(value):
    receipt_type = value[:2]
    return receipt_type


@register.filter
def receipt_ref(value):
    if value:
        receipt_ref_length = len(value)
        if value.startswith("Pago"):
            return value[: receipt_ref_length // 2]
    else:
        value = "Pago"
    return value


@register.filter
def format_date(value):
    date = datetime.strptime(value, "%Y-%m-%d").date()
    return date.strftime("%d/%m/%Y")


@register.filter
def balance(value):
    balance = 0.0
    balance += float(value)
    return balance
