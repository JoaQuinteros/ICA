from typing import Any, Dict, List

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from odoo.forms import BaseClaimForm, LoginForm
from odoo.tasks import get_client_data, get_contract_data, get_client_tickets, valid_change_speed_open, valid_admin_open, valid_service_open, valid_unsuscribe_open, valid_change_adress_open

# from odoo.models import Client, Service


REASON_CHOICES: Dict[str, Any] = {
    "technical": "Reclamo técnico",
    "request_change_of_address": "Solicitar cambio de domicilio",
    "admin": "Consultas administrativas u otras consultas",
    "change_plan": "Cambiar de plan",
    "request_unsubscribe": "Solicitar baja"
}


def index_view(request: HttpRequest, dni: str) -> HttpResponse:
    context: Dict[str, Any] = {}
    context["page"] = "Cliente"
    client: Dict[str, Any] = get_client_data(dni)
    if client:
        context["client"] = client
        contract_ids: List[str] = client.get('contract_ids')  # Se crea una lista con los "ID" de los contratos asociados al Cliente.
        contracts_list: List[Dict] = []  # Lista de diccionarios con la información de los contratos.
        for contract_id in contract_ids:
            contract: Dict[str, Any] = get_contract_data(contract_id)  # Se busca la información de cada contrato.
            contracts_list.append(contract)  # Se agrega la información de cada contrato a la lista "contracts_list".
        context["contracts_list"] = contracts_list  # Se envía al contexto la lista de contratos creada.

        context["payment_url"] = f"http://link.integralcomunicaciones.com:4000/linkpago/{client.get('internal_code')}"
    else:
        messages.info(request, 'No se encontró el cliente buscado.')
        return redirect('login')
    # client = Client.objects.get(dni=dni)
    return render(request, 'index.html', context)

def login_view(request: HttpRequest) -> HttpResponse:
    context: Dict[str, Any] = {}
    context["page"] = "Login"
    form = LoginForm(request.POST or None)
    context["form"] = form
    if request.method == 'POST':
        if form.is_valid():
            dni: str = form.cleaned_data.get('dni')
            return redirect('index', dni)
    return render(request, 'login.html', context)


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
    form = BaseClaimForm(request.POST or None, initial=data, reason_type = claim_type)
    context["form"] = form
    context["ticket_open"] = False 
    if claim_type == "technical" and service_open is not False:
        context["ticket_open"] = service_open
        
    elif claim_type == "admin" and admin_open is not False:
        context["ticket_open"] = admin_open

    elif claim_type == "change_plan" and change_plan_open is not False:
        context["ticket_open"] = change_plan_open
    
    elif claim_type == "request_unsubscribe" and change_plan_open is not False:
        context["ticket_open"] = unsuscribe_plan_open

    elif claim_type == "request_change_of_address" and change_plan_open is not False:
        context["ticket_open"] = change_adress_open
    
    context["dni"] = dni
    context["id"] = id
    contract: Dict[str, Any] = get_contract_data(id)
    context["contract"] = contract
    # form = BaseClaimForm(request.POST or None)
    # context["form"] = form    
    # if request.method == "POST":
    #     if form.is_valid():
    #         # name: str = form.cleaned_data.get('name')
    #         # phone_number: str = form.cleaned_data.get('phone_number')
    #         # email: str = form.cleaned_data.get('email')
    #         # files = form.cleaned_data.get('files')
    #         comment: str = request.POST.get('description')
    #         context['dni'] = request.POST.get('dni')
    #         context['id'] = request.POST.get('id')
    #         # print(name)
    #         # print(phone_number)
    #         # print(email)
    #         # print(files)
    #         # form.instance.service = service
    #         # form.save()
    #         # Cuando se crea un nuevo reclamo, el servicio pasa a tener un reclamo activo.
    #         # service.has_active_claim = True
    #         # service.save()
    #         #messages.success(request, "El reclamo se registró de forma exitosa.")
    #         return redirect('index', dni)
    return render(request, 'claim_form.html', context)

def process_claim_view(request: HttpRequest) -> HttpResponse:
    context: Dict[str, Any] = {}
    form = LoginForm(request.POST or None)
    context["form"] = form
    if request.method == 'POST':
        if form.is_valid():
            name:str = form.cleaned_data.get('name')
            phone_number:str = form.cleaned_data.get('phone_number')
            email:str = form.cleaned_data.get('email')
            files:files = form.cleaned_data.get('files')
            comment: str = request.POST.get('description')
            print(name)
            print(phone_number)
            print(email)
            context['dni'] = request.POST.get('dni')
            context['id'] = request.POST.get('id')
            dni: str = request.POST.get('dni')
            id: int = request.POST.get('id')
            messages.success(request, "El reclamo se registró de forma exitosa.")
            return redirect('claim_create', dni, id)
    return redirect('claim_create', dni, id)

def process_comment_view(request: HttpRequest) -> HttpResponse:
    context: Dict[str, Any] = {}
    form = LoginForm(request.POST or None)
    context["form"] = form
    if request.method == 'POST':
        if form.is_valid():
            comment: str = request.POST.get('description')
            context['dni'] = request.POST.get('dni')
            context['id'] = request.POST.get('id')
            dni: str = request.POST.get('dni')
            id: int = request.POST.get('id')
            messages.success(request, "El reclamo se registró de forma exitosa.")
            return redirect('claim_create', dni, id)
    return redirect('claim_create', dni, id)