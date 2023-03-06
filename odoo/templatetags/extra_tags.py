from datetime import datetime

from django import template

register = template.Library()


@register.filter
def receipt_type(value: str) -> str:
    receipt_type = value[:2]
    receipt_type_dict = {
        "ND" : "Nota de débito",
        "FA" : "Factura",
        "RE" : "Recibo",
        "CP" : "Cupón de pago",
    }
    return receipt_type_dict.get(receipt_type)


@register.filter
def receipt_number(value: str) -> str:
    return value[3:]


@register.filter
def receipt_ref(value: str) -> str:
    receipt_ref_length = len(value)
    if value.startswith("Pago"):
        return value[0:receipt_ref_length//2]
    return value


@register.filter
def format_date(value: str) -> str:
    date = datetime.strptime(value, "%Y-%m-%d").date()
    return date.strftime("%d/%m/%Y")


@register.filter
def get_download_url(access_token: str, id: str):
    return f"https://gestion.integralcomunicaciones.com/my/invoices/{id}?access_token={access_token}&report_type=pdf&download=true"