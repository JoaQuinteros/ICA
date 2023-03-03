from typing import Any, Dict, List

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from odoo.forms import ClaimForm, ClaimForm2, LoginForm
from odoo.tasks import get_client_data, get_contract_data

# from odoo.models import Client, Service


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
    context["dni"] = dni
    contract: Dict[str, Any] = get_contract_data(id)
    context["contract"] = contract
    form = ClaimForm(request.POST or None)
    context["form"] = form
    if request.method == "POST":
        if form.is_valid():
            # form.instance.service = service
            # form.save()
            # Cuando se crea un nuevo reclamo, el servicio pasa a tener un reclamo activo.
            # service.has_active_claim = True
            # service.save()
            messages.success(request, "El reclamo se registró de forma exitosa.")
            return redirect('index', dni)
    return render(request, 'claim_form.html', context)



