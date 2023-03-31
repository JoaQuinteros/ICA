from typing import Any, Dict, List

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from odoo.forms import BaseClaimForm, LoginForm, AddInfoCalimForm
from odoo.tasks import get_account_data, get_client_data, get_contract_data
import re
import os
from django.core.files import File
from django.conf import settings
from odoo.tasks import (
    get_account_data,
    get_account_line_data,
    get_client_data,
    get_client_tickets,
    get_contract_data,
    valid_admin_open,
    valid_change_adress_open,
    valid_change_speed_open,
    valid_service_open,
    valid_unsuscribe_open,
    save_claim,
    add_info_claim,

)
from datetime import datetime

# from odoo.models import Client, Service


REASON_CHOICES: Dict[str, Any] = {
    "technical": "Reclamo técnico",
    "request_change_of_address": "Solicitar cambio de domicilio",
    "admin": "Consultas administrativas u otras consultas",
    "change_plan": "Cambiar de plan",
    "request_unsubscribe": "Solicitar baja",
}


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
    tickets_open: Dict[str, Any] = get_client_tickets(id)
    # validaciónes en odoo si tiene un reclamo de ese tipo abierto.
    admin_open = valid_admin_open(tickets_open)
    service_open = valid_service_open(tickets_open)
    change_plan_open = valid_change_speed_open(tickets_open)
    unsuscribe_plan_open = valid_unsuscribe_open(tickets_open)
    change_adress_open = valid_change_adress_open(tickets_open)
    form = BaseClaimForm(request.POST or None, request.FILES or None,initial=data, reason_type = claim_type, id = id)
    formAddInfo = AddInfoCalimForm(request.POST or None, request.FILES or None,initial=data, reason_type = claim_type, id = id)
    context["form"] = form
    context["formAddInfo"] = formAddInfo
    context["ticket_open"] = False
    print(context["ticket_open"]) 
    if claim_type == 'technical' and service_open != False:
        context["ticket_open"] = service_open
        
    if claim_type == "admin" and admin_open != False:
        context["ticket_open"] = admin_open

    if claim_type == "change_plan" and change_plan_open != False:
        context["ticket_open"] = change_plan_open
    
    if claim_type == "request_unsubscribe" and unsuscribe_plan_open != False:
        context["ticket_open"] = unsuscribe_plan_open

    if claim_type == "request_change_of_address" and change_adress_open != False:
        context["ticket_open"] = change_adress_open

    tickets_open = context["ticket_open"]
    context["dni"] = dni
    context["id"] = id
    contract: Dict[str, Any] = get_contract_data(id)
    context["contract"] = contract
    if request.method == "POST":
        if tickets_open is False:
            if form.is_valid():
                dni = request.POST.get('dni')
                id = request.POST.get('id')
                name: str = form.cleaned_data.get('name')
                phone_number: str = form.cleaned_data.get('phone_number')
                email: str = form.cleaned_data.get('email')
                description: str = form.cleaned_data.get('description')
                files = None
                if request.FILES:
                    files = request.FILES['files']
                save_claim(dni, id, phone_number, email, description, files)
                messages.success(request, "El reclamo se registró de forma exitosa.")
            else:
                messages.error(request, "El reclamo no se registró hay error en los datos ingresados.")
        else:
            if formAddInfo.is_valid():
                print("VALIDO POR ACA")
                dni = request.POST.get('dni')
                id = request.POST.get('id')
                description: str = formAddInfo.cleaned_data.get('description')
                print(description)
                files = None
                if request.FILES:
                    files = request.FILES['files']
                add_info_claim(dni, id, description)
                messages.success(request, "El reclamo se registró de forma exitosa.")
            else:
                messages.error(request, "El reclamo no se registró hay error en los datos ingresados.")
    # # form.instance.service = service
    #         # form.save()
    #         # Cuando se crea un nuevo reclamo, el servicio pasa a tener un reclamo activo.
    #         # service.has_active_claim = True
    #         # service.save()
    #         #messages.success(request, "El reclamo se registró de forma exitosa.")
    #         return redirect('index', dni)
    return render(request, "claim_form.html", context)



def account_move_list_view(request: HttpRequest, dni: str) -> HttpResponse:
    context: Dict[str, Any] = {}
    context['today'] = datetime.now().date()
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
        account_move_line_list: List[Dict] = get_account_line_data(client_id)
        #for account_move in reversed(account_move_list):
        for account_move_line in reversed(account_move_line_list):
            balance = balance + (account_move_line.get('debit') - account_move_line.get('credit'))
            account_move_line['balance'] = round(balance, 2)
            print(account_move_line)
        paginator = Paginator(account_move_line_list, 10)
        page_number: str = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj
        return render(request, "account_move_list.html", context)
    else:
        messages.info(request, "No se encontró el cliente buscado.")
        return redirect("index", dni)
