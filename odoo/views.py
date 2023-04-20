from datetime import datetime

from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from odoo.forms import AddClaimInfoForm, BaseClaimForm, LoginForm, LoginRecoveryForm
from odoo.tasks import (
    add_info_claim,
    fetch_all_data,
    fetch_contract_open_tickets,
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


async def index_view(request, dni):
    client = cache.get(f"{dni}")

    if not client:
        await fetch_all_data(dni)
        client = cache.get(f"{dni}")

    if client == "Not found":
        messages.info(request, "No se encontró el cliente buscado.")
        return redirect("login")

    contracts_list = cache.get(f"{dni}").get("contracts_list")

    if not contracts_list:
        messages.info(request, "El cliente no posee contratos.")
        return redirect("login")

    context = {
        "page": "Cliente",
        "contracts_list": contracts_list,
        "client": client,
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
    context = {}
    client_data = cache.get(f"{dni}")
    claim_type = request.GET.get("claim_type")
    open_tickets_list = fetch_contract_open_tickets(contract_id)

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
        )

        if open_tickets_list:
            for open_ticket in open_tickets_list:
                ticket_type_id = open_ticket.get("category_id")[0]
                if claim_type == ticket_type_id:
                    form = BaseClaimForm(
                        request.POST or None,
                        request.FILES or None,
                        claim_type=claim_type,
                        has_open_ticket=True,
                    )

        context["form"] = form
        context["selected_reason"] = int(claim_type)

    # formAddInfo = AddClaimInfoForm(
    #     request.POST or None,
    #     request.FILES or None,
    #     initial={"reason": claim_type},
    #     reason_type=claim_type,
    #     id=contract_id,
    # )

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

    contracts_list = client_data.get("contracts_list")
    for contract in contracts_list:
        if contract.get("id") == contract_id:
            context["contract"] = contract

    if request.method == "POST":
        if not open_tickets_list:
            if form.is_valid():
                dni = request.POST.get("dni")
                id = request.POST.get("id")
                name: str = form.cleaned_data.get("name")
                phone_number: str = form.cleaned_data.get("phone_number")
                email: str = form.cleaned_data.get("email")
                description: str = form.cleaned_data.get("description")
                files = None
                if request.FILES:
                    files = request.FILES["files"]
                if claim_type == "technical":
                    save_claim(dni, id, 34, phone_number, email, description, files)
                    messages.success(
                        request, "El reclamo se registró de forma exitosa."
                    )
                if claim_type == "admin":
                    save_claim(dni, id, 41, phone_number, email, description, files)
                    messages.success(
                        request, "La consulta se registró de forma exitosa."
                    )
                if claim_type == "change_plan":
                    save_claim(dni, id, 45, phone_number, email, description, files)
                    messages.success(
                        request, "La solicitud se registró de forma exitosa."
                    )
                if claim_type == "request_unsubscribe":
                    save_claim(dni, id, 56, phone_number, email, description, files)
                    messages.success(
                        request, "La solicitud se registró de forma exitosa."
                    )
                if claim_type == "request_change_of_address":
                    save_claim(dni, id, 36, phone_number, email, description, files)
                    messages.success(
                        request, "La solicitud se registró de forma exitosa."
                    )
            else:
                messages.error(
                    request,
                    "El reclamo o solicitud no se registró hay error en los datos ingresados.",
                )
            # else:
            #     if formAddInfo.is_valid():
            #         dni = request.POST.get("dni")
            #         id = request.POST.get("id")
            #         id_ticket = request.POST.get("id_ticket")
            #         ticket_description = request.POST.get("ticket_description")
            #         description: str = formAddInfo.cleaned_data.get("description")
            #         files = None
            #         if request.FILES:
            #             files = request.FILES["files"]
            #         add_info_claim(
            #             dni, id, id_ticket, ticket_description, description, files
            #         )
            #         messages.success(request, "El reclamo se registró de forma exitosa.")
            #     else:
            #         messages.error(
            #             request,
            #             "El reclamo no se registró hay error en los datos ingresados.",
            #         )
    # # form.instance.service = service
    #         # form.save()
    #         # Cuando se crea un nuevo reclamo, el servicio pasa a tener un reclamo activo.
    #         # service.has_active_claim = True
    #         # service.save()
    #         #messages.success(request, "El reclamo se registró de forma exitosa.")
    #         return redirect('index', dni)

    context["client"] = client_data
    context["reason_choices"] = REASON_CHOICES
    context["page"] = "Reclamo"
    return render(request, "claim_form.html", context)


def account_movements_list_view(request, dni):
    client_data = cache.get(f"{dni}")
    client_id = client_data.get("id")

    if client_id:
        initial_balance = cache.get(f"{dni}").get("initial_balance")

        balance_credit = initial_balance.get("credit")
        balance_debit = initial_balance.get("debit")
        balance = 0.0

        if balance_credit:
            balance -= balance_credit
        elif balance_debit:
            balance += balance_debit

        account_movements = cache.get(f"{dni}").get("account_movements")
        filtered_account_movements = []
        names = []

        for account_movement in account_movements:
            receipt_type = account_movement.get("name")
            if receipt_type not in names:
                filtered_account_movements.append(account_movement)
                names.append(receipt_type)

        for account_movement in reversed(filtered_account_movements):
            amount_total = account_movement.get("amount_total")
            receipt_type = account_movement.get("name")

            if receipt_type.startswith("RE") or receipt_type.startswith("NC"):
                balance -= float(amount_total)
            else:
                balance += float(amount_total)
            account_movement["balance"] = round(balance, 2)

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
    else:
        messages.info(request, "No se encontró el cliente buscado.")
        return redirect("index", dni)
