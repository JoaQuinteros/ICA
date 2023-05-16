from datetime import datetime
import re
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
def format_date(value: str) -> str:
    date: datetime = datetime.strptime(value, "%Y-%m-%d").date()
    return date.strftime("%d/%m/%Y")


@register.filter
def balance(value):
    balance = 0.0
    balance += float(value)
    return balance

@register.filter
def format_claim(value):
    unformatted_string = re.compile("<.*?>")
    description_clean = value.replace("<br>", "\n")
    value_clean = re.sub(
             unformatted_string, "", description_clean
         )
    return value_clean

@register.filter
def format_date_due(value:datetime) -> str:
    return value.strftime("%d/%m/%Y")