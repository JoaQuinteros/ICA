from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from odoo.forms import BaseClaimForm, LoginForm, LoginRecoveryForm
from odoo.tasks import (
    fetch_account_movements,
    fetch_client_data,
    fetch_contract_open_tickets,
    fetch_contracts_list,
    fetch_initial_balance,
    save_claim,
    valid_admin_open,
    valid_change_adress_open,
    valid_change_speed_open,
    valid_service_open,
    valid_unsuscribe_open,
)

REASON_CHOICES = {
    34: "Reclamo técnico",
    36: "Solicitar cambio de domicilio",
    41: "Consultas administrativas u otras consultas",
    45: "Cambiar de plan",
    56: "Solicitar baja",
}


def index_view(request, dni):
    client_data = fetch_client_data(dni)
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
        return redirect("index", dni)

    context = {
        "page": "Login",
        "form": form,
    }
    return render(request, "login.html", context)


def login_recovery_view(request):
    form = LoginRecoveryForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        dni = form.cleaned_data.get("dni")
        return redirect("index", dni)

    context = {
        "page": "Recuperación",
        "form": form,
    }
    return render(request, "recovery_form.html", context)


def claim_create_view(request, dni, contract_id):
    client_data = fetch_client_data(dni)

    context = {
        "client": client_data,
        "reason_choices": REASON_CHOICES,
        "page": "Reclamo",
    }

    claim_type = request.GET.get("claim_type")
    open_tickets_list = fetch_contract_open_tickets(contract_id)
    open_ticket = {"id": 561651, "portal_description": "sarasa"}

    # if open_tickets_list:
    # admin_open = valid_admin_open(open_tickets_list)
    # service_open = valid_service_open(tickets_open)
    # change_plan_open = valid_change_speed_open(tickets_open)
    # unsuscribe_plan_open = valid_unsuscribe_open(tickets_open)
    # change_adress_open = valid_change_adress_open(tickets_open)

    if claim_type:
        form = BaseClaimForm(
            request.POST or None,
            request.FILES or None,
            claim_type=claim_type,
            has_open_ticket=True,
        )

        if open_tickets_list:
            for ticket in open_tickets_list:
                ticket_type_id = ticket.get("category_id")[0]
                if claim_type == ticket_type_id:
                    open_ticket = ticket
                    form = BaseClaimForm(
                        request.POST or None,
                        request.FILES or None,
                        claim_type=claim_type,
                        has_open_ticket=True,
                    )

        context["form"] = form
        context["selected_reason"] = int(claim_type)
        context["open_ticket"] = open_ticket

    # context["formAddInfo"] = formAddInfo
    # context["ticket_open"] = None
    # if claim_type == "technical" and service_open != False:
    #     context["ticket_open"] = service_open

    # if claim_type == "admin" and admin_open != False:
    #     context["ticket_open"] = admin_open

    # if claim_type == "change_plan" and change_plan_open != False:
    #     context["ticket_open"] = change_plan_open

    # if claim_type == "request_unsubscribe" and unsuscribe_plan_open != False:
    #     context["ticket_open"] = unsuscribe_plan_open

    # if claim_type == "request_change_of_address" and change_adress_open != False:
    #     context["ticket_open"] = change_adress_open

    contracts_list = fetch_contracts_list(client_data.get("contract_ids"))
    for contract in contracts_list:
        if contract.get("id") == contract_id:
            context["contract"] = contract

    if request.method == "POST":
        if form.is_valid():
            form_data = form.cleaned_data.copy()
            form_data["partner_id"] = client_data.get("id")
            form_data["contract_id"] = contract_id
            form_data["category_id"] = int(claim_type)
            form_data["files"] = request.FILES.get("files")
            form_data["open_ticket_id"] = open_ticket.get("id")

            save_claim(form_data)

            if claim_type == "34":
                message = "El reclamo se registró de forma exitosa."
            elif claim_type in ["36", "45", "56"]:
                message = "La solicitud se registró de forma exitosa."
            if claim_type == "41":
                message = "La consulta se registró de forma exitosa."

            messages.success(request, message)
            return redirect("index", dni)

    return render(request, "claim_form.html", context)


def get_download_url(access_token, id):
    return f"https://gestion.integralcomunicaciones.com/my/invoices/{id}?access_token={access_token}"


def account_movements_list_view(request, dni):
    client_data = fetch_client_data(dni)
    client_id = client_data.get("id")
    initial_balance = fetch_initial_balance(client_id)
    account_movements = fetch_account_movements(client_id)

    balance_credit = initial_balance.get("credit")
    balance_debit = initial_balance.get("debit")
    balance = 0.0

    if balance_credit:
        balance -= balance_credit
    elif balance_debit:
        balance += balance_debit

    filtered_account_movements = []
    names = []

    for account_movement in account_movements:
        receipt_type = account_movement.get("name")
        if receipt_type not in names:
            filtered_account_movements.append(account_movement)
            names.append(receipt_type)

    for account_movement in reversed(filtered_account_movements):
        movement_id = account_movement.get("id")
        amount_total = account_movement.get("amount_total")
        receipt_type = account_movement.get("name")
        access_token = account_movement.get("access_token")

        if receipt_type.startswith("RE") or receipt_type.startswith("NC"):
            balance -= float(amount_total)
        else:
            balance += float(amount_total)
        account_movement["balance"] = round(balance, 2)

        if access_token:
            account_movement["download_url"] = get_download_url(
                access_token, movement_id
            )

    paginator = Paginator(filtered_account_movements, 20)
    page_number: str = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "today": datetime.now().date(),
        "page": "Movimientos",
        "client": client_data,
        "payment_url": f"http://link.integralcomunicaciones.com:4000/linkpago/{client_data.get('internal_code')}",
        "page_obj": page_obj,
        "initial_balance": initial_balance,
    }
    return render(request, "account_movements_list.html", context)
