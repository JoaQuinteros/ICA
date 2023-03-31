from datetime import datetime

from django import template

register = template.Library()


@register.filter
def receipt_type(value: str) -> str:
    receipt_type: str = value[:2]
    return receipt_type


@register.filter
def receipt_ref(value: str) -> str:
    if value:
        receipt_ref_length: int = len(value)
        if value.startswith("Pago"):
            return value[0 : receipt_ref_length // 2]
    else:
        value = "Pago"
    return value 


@register.filter
def format_date(value: str) -> str:
    date: datetime = datetime.strptime(value, "%Y-%m-%d").date()
    return date.strftime("%d/%m/%Y")


@register.filter
def get_download_url(access_token: str, id: str):
    return f"https://gestion.integralcomunicaciones.com/my/invoices/{id}?access_token={access_token}"


@register.filter
def balance(value: str) -> str:
    balance: float = 0.0
    balance += float(value)
    return balance

@register.filter
def format_date_due(value:datetime) -> str:
    return value.strftime("%d/%m/%Y")