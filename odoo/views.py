from typing import Any, Dict, List

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from odoo.forms import BaseClaimForm, ClaimForm2, LoginForm, TechnicalClaimForm
from odoo.tasks import get_account_data, get_client_data, get_contract_data

# from odoo.models import Client, Service


REASON_CHOICES: Dict[str, Any] = {"technical": "Técnico", "admin": "Administrativo"}


def index_view(request: HttpRequest, dni: str) -> HttpResponse:
    context: Dict[str, Any] = {}
    context["page"] = "Cliente"
    client: Dict[str, Any] = get_client_data(dni)
    if client:
        context["client"] = client
        contract_ids: List[str] = client.get(
            "contract_ids"
        )  # Se crea una lista con los "ID" de los contratos asociados al Cliente.
        contracts_list: List[
            Dict
        ] = []  # Lista de diccionarios con la información de los contratos.
        for contract_id in contract_ids:
            contract: Dict[str, Any] = get_contract_data(
                contract_id
            )  # Se busca la información de cada contrato.
            contracts_list.append(
                contract
            )  # Se agrega la información de cada contrato a la lista "contracts_list".
        context[
            "contracts_list"
        ] = contracts_list  # Se envía al contexto la lista de contratos creada.
    else:
        messages.info(request, "No se encontró el cliente buscado.")
        return redirect("login")
    # client = Client.objects.get(dni=dni)
    return render(request, "index.html", context)


def login_view(request: HttpRequest) -> HttpResponse:
    context: Dict[str, Any] = {}
    context["page"] = "Login"
    form = LoginForm(request.POST or None)
    context["form"] = form
    if request.method == "POST":
        if form.is_valid():
            dni: str = form.cleaned_data.get("dni")
            return redirect("index", dni)
    return render(request, "login.html", context)


def claim_create_view(request: HttpRequest, dni: str, id: int) -> HttpResponse:
    context: Dict[str, Any] = {}
    context["page"] = "Reclamo"
    # service = Service.objects.get(pk=id)

    context["reason_choices"] = REASON_CHOICES

    claim_type: str = request.GET.get("reason")
    data: Dict[str, str] = {"reason": claim_type}
    context["selected_reason"] = claim_type
    has_open_claim = (
        False  # Hacer la validación en odoo si tiene un reclamo de ese tipo abierto.
    )
    if claim_type == "technical":
        form = TechnicalClaimForm(
            request.POST or None, initial=data, has_open_claim=has_open_claim
        )
        context["form"] = form
    elif claim_type == "admin":
        form = BaseClaimForm(
            request.POST or None, initial=data, has_open_claim=has_open_claim
        )
        context["form"] = form

    context["dni"] = dni
    contract: Dict[str, Any] = get_contract_data(id)
    context["contract"] = contract
    # form = BaseClaimForm(request.POST or None)
    # context["form"] = form
    if request.method == "POST":
        if form.is_valid():
            # form.instance.service = service
            # form.save()
            # Cuando se crea un nuevo reclamo, el servicio pasa a tener un reclamo activo.
            # service.has_active_claim = True
            # service.save()
            messages.success(request, "El reclamo se registró de forma exitosa.")
            return redirect("index", dni)
    return render(request, "claim_form.html", context)


def account_move_list_view(request: HttpRequest, dni: str) -> HttpResponse:
    context: Dict[str, Any] = {}
    context["page"] = "Movimientos"
    client_data: Dict[str, Any] = get_client_data(dni)
    context["client"] = client_data
    client_id: str = client_data.get("id")
    context[
        "payment_url"
    ] = f"http://link.integralcomunicaciones.com:4000/linkpago/{client_data.get('internal_code')}"
    if client_id:
        account_move_list: List[Dict] = get_account_data(client_id)
        balance: float = 0.0
        for account_move in reversed(account_move_list):
            receipt_type: str = account_move.get("name")
            amount_total: str = account_move.get("amount_total")
            if receipt_type.startswith("RE"):
                balance -= float(amount_total)
            else:
                balance += float(amount_total)
            account_move["balance"] = round(balance, 2)
        paginator = Paginator(account_move_list, 10)
        page_number: str = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj
        return render(request, "account_move_list.html", context)
    else:
        messages.info(request, "No se encontró el cliente buscado.")
        return redirect("index", dni)
