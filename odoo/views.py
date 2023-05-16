from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect, render

from odoo.forms import BaseClaimForm, LoginForm, LoginRecoveryForm
from odoo.tasks import (
    fetch_account_movements,
    fetch_client_data,
    fetch_contract_open_tickets,
    fetch_contracts_list,
    save_claim,
    save_recovery,
    fetch_account_move_lines,
    fetch_get_account_move,
    fetch_client_validate_data,
)

REASON_CHOICES = {
    34: "Reclamo técnico",
    36: "Solicitar cambio de domicilio",
    41: "Consultas administrativas u otras consultas",
    45: "Cambiar de plan",
    56: "Solicitar baja",
}


def index_view(request, dni, internal_code):
    client_data = fetch_client_validate_data(dni, internal_code)
    if not client_data:
        messages.info(request, "No se encontró el cliente buscado.")
        return redirect("login")

    contracts_list = fetch_contracts_list(client_data.get("contract_ids"))
    if not contracts_list:
        messages.info(request, "El cliente no posee contratos.")
        return redirect("login")

    context = {
        "page": "Cliente",
        "client": client_data,
        "contracts_list": contracts_list,
    }
    return render(request, "index.html", context)


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        dni = form.cleaned_data.get("dni")
        internal_code = form.cleaned_data.get("internal_code")
        return redirect("index", dni, internal_code)

    context = {
        "page": "Consulta",
        "form": form,
    }
    return render(request, "login.html", context)


def login_recovery_view(request):
    form = LoginRecoveryForm(request.POST or None)
    context = {
        "page": "Recuperación",
        "form": form,
    }
    if request.method == "POST" and form.is_valid():
        form_data = form.cleaned_data.copy()
        save_recovery(form_data)
        messages.success(request, "La solicitud se registró de forma exitosa.")
        return redirect("login")
    return render(request, "recovery_form.html", context)


def claim_create_view(request, dni, contract_id):
    client_data = fetch_client_data(dni)
    are_open_ticket = False
    open_ticket = None

    context = {
        "page": "Reclamo",
        "client": client_data,
        "reason_choices": REASON_CHOICES,
    }

    claim_type = request.GET.get("claim_type")
    open_tickets_list = fetch_contract_open_tickets(contract_id)

    if claim_type:
        form = BaseClaimForm(
            request.POST or None,
            request.FILES or None,
            claim_type=claim_type,
        )

        if open_tickets_list:
            for ticket in open_tickets_list:
                ticket_type_id = ticket.get("category_id")[0]
                if int(claim_type) == int(ticket_type_id):
                    open_ticket = ticket
                    form = BaseClaimForm(
                        request.POST or None,
                        request.FILES or None,
                        claim_type=claim_type,
                        has_open_ticket=True,
                    )
                    are_open_ticket = True

        context["open_ticket"] = open_ticket
        context["form"] = form
        context["selected_reason"] = int(claim_type)

    context["are_open_ticket"] = are_open_ticket
    contracts_list = fetch_contracts_list(client_data.get("contract_ids"))
    for contract in contracts_list:
        if contract.get("id") == contract_id:
            context["contract"] = contract

    if request.method == "POST":
        print(request.GET.get("claim_type"))
        if form.is_valid():
            form_data = form.cleaned_data.copy()
            form_data["partner_id"] = client_data.get("id")
            form_data["contract_id"] = contract_id
            form_data["category_id"] = int(claim_type)
            form_data["files"] = request.FILES
            if open_ticket:
                form_data["open_ticket_id"] = open_ticket.get("id")

            save_claim(form_data, open_ticket)

            if claim_type == "34":
                message = "El reclamo se registró de forma exitosa."
            elif claim_type in ["36", "45", "56"]:
                message = "La solicitud se registró de forma exitosa."
            if claim_type == "41":
                message = "La consulta se registró de forma exitosa."

            messages.success(request, message)
            # return redirect("create_claim", dni=dni, contract_id=contract_id)
            return redirect(
                "/claim/"
                + str(dni)
                + "/"
                + str(contract_id)
                + "/?claim_type="
                + str(claim_type)
            )
        else:
            messages.error(request, "Los datos ingresados son incorrectos")
            return render(request, "claim_form.html", context)

    return render(request, "claim_form.html", context)

def account_movements_list_view(request, dni):

    client_data = fetch_client_data(dni)
    client_id: str = client_data.get("id")
    internal_code: str = client_data.get("internal_code") 
    if client_id:
        context = fetch_get_account_move(request, client_id, client_data)
        return render(request, "account_movements_list.html", context)
    else:
        messages.info(request, "No se encontró el cliente buscado.")
        return redirect("index", dni, internal_code)