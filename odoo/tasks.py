import os.path
import re
from base64 import b64encode
from datetime import datetime
from django.core.paginator import Paginator
import odoolib
import requests
from decouple import config
from django.core.exceptions import ValidationError


def get_connection():
    try:
        connection = odoolib.get_connection(
            hostname=config("ODOO_DB_HOSTNAME"),
            database=config("ODOO_DB_NAME"),
            login=config("ODOO_DB_LOGIN"),
            password=config("ODOO_DB_PASSWORD"),
            port=443,
            protocol="jsonrpcs",
        )
        return connection
    except (
        requests.exceptions.ConnectionError,
        odoolib.main.AuthenticationError,
        odoolib.main.JsonRPCException,
    ):
        raise ValidationError("No pudimos procesar tu pedido.")


def fetch_client_data(dni):
    connection = get_connection()
    client_model = connection.get_model("res.partner")
    client_data = client_model.search_read(
            [("vat", "=", dni)],
            ["id", "internal_code", "name", "email", "vat", "contract_ids", "credit"],
        )[0]
    if client_data.get("email"):
        email = client_data.get("email")
        email_list_separator = email.find(";")
        if email_list_separator:
            client_data["email"] = email[:email_list_separator]
    else:
        client_data["email"] = ''
            
    return client_data

def fetch_client_validate_data(dni, internal_code):
    connection = get_connection()
    client_model = connection.get_model("res.partner")
    if client_model.search_read(
        [("vat", "=", dni),("internal_code", "=", internal_code)],
        ["id", "internal_code", "name", "email", "vat", "contract_ids", "credit"],):
        client_data = client_model.search_read(
            [("vat", "=", dni),("internal_code", "=", internal_code)],
            ["id", "internal_code", "name", "email", "vat", "contract_ids", "credit"],
        )[0]
        if client_data.get("email"):
            email = client_data.get("email")
            email_list_separator = email.find(";")
            if email_list_separator:
                client_data["email"] = email[:email_list_separator]
        else:
            client_data["email"] = ''
                
        return client_data
    return False


def fetch_contracts_list(contract_ids):
    connection = get_connection()
    contract_model = connection.get_model("contract.contract")
    contracts_list = []

    for id in contract_ids:
        contract_data = contract_model.search_read(
            [("id", "=", id)],
            [
                "id",
                "active",
                "is_terminated",
                "domicilio",
                "localidad",
                "latitud",
                "longitud",
                "ssid_id",
                "sistema_autonomo_id",
                "servicio_suspendido",
                "ssid_state",
            ],
        )[0]

        if contract_data:
            domicilio = contract_data.get("domicilio")
            coords_parenthesis = domicilio.rfind("(")
            if coords_parenthesis:
                contract_data["domicilio"] = domicilio[:coords_parenthesis]
            first_dash = domicilio.find("-")
            if first_dash:
                contract_data["domicilio"] = domicilio[:first_dash]
            contracts_list.append(contract_data)

    return contracts_list


def fetch_contract_open_tickets(contract_id):
    connection = get_connection()
    closed_ticket_ids_list = fetch_closed_ticket_ids(connection)

    ticket_model = connection.get_model("helpdesk.ticket")
    open_tickets_list = ticket_model.search_read(
        [
            ("suscripcion_id", "=", contract_id),
            ("stage_id", "!=", closed_ticket_ids_list),
            ("create_uid", "=", 27),
        ],
        [
            "id",
            "number",
            "portal_description",
            "stage_id",
            "partner_id",
            "stage_id",
            "category_id",
            "suscripcion_id",
        ],
    )

    return open_tickets_list


def fetch_closed_ticket_ids(connection):
    closed_tickets_model = connection.get_model("helpdesk.ticket.stage")
    closed_tickets_list = closed_tickets_model.search_read([("closed", "=", True)])

    closed_ticket_ids_list = []
    for closed_ticket in closed_tickets_list:
        closed_ticket_ids_list.append(closed_ticket.get("id"))

    return closed_ticket_ids_list


def format_ticket_description(ticket):
    unformatted_string = re.compile("<.*?>")
    if ticket.get("portal_description"):
        description_clean = ticket["portal_description"].replace("<br>", "\n")
        ticket["portal_description"] = re.sub(unformatted_string, "", description_clean)
        return ticket


def fetch_account_movements(client_id):
    connection = get_connection()
    account_model = connection.get_model("account.move")
    account_movements_list = account_model.search_read(
        [("partner_id", "=", client_id), ("state", "=", "posted")],
        [
            "id",
            "ref",
            "partner_id",
            "date",
            "invoice_date_due",
            "amount_total",
            "amount_residual",
            "invoice_payment_state",
            "name",
            "access_token",
        ],
    )
    return account_movements_list


# def fetch_initial_balance(client_id):
#     connection = get_connection()
#     account_movement_model = connection.get_model("account.move.line")
#     initial_balance = account_movement_model.search_read(
#         [
#             ("partner_id", "=", client_id),
#             ("account_id", "=", 6),
#             ("parent_state", "=", "posted"),
#         ],
#         [
#             "ref",
#             "date",
#             "move_id",
#             "debit",
#             "credit",
#         ],
#     )[-1]
#     return initial_balance

def fetch_account_move_lines(client_id):
    connection = get_connection()
    account_movement_model = connection.get_model("account.move.line")
    account_move_line = account_movement_model.search_read(
        [
            ("partner_id", "=", client_id),
            ("account_id", "=", 6),
            ("parent_state", "=", "posted"),
        ],
        [
            "ref",
            "date",
            "move_id",
            "debit",
            "credit",
        ],
    )
    return account_move_line

def get_download_url(access_token, id):
    return f"https://gestion.integralcomunicaciones.com/my/invoices/{id}?access_token={access_token}"

def fetch_get_account_move (request, client_id, client_data):
    context = {
    "today": datetime.now().date(),
    "page": "Movimientos",
    "client": client_data,
    "payment_url": f"http://link.integralcomunicaciones.com:4000/linkpago/{client_data.get('internal_code')}",
    "page_obj": False,
    }
    account_move_line_list = fetch_account_move_lines(client_id)
    account_movements_list = fetch_account_movements(client_id)
    balance: float = 0.0
    if account_move_line_list:
        for account_move_line in account_move_line_list:
            print(account_move_line)
            if account_move_line.get('move_id')[0] is not None:
                for account_move in account_movements_list:
                    if int(account_move.get('id')) == int(account_move_line.get('move_id')[0]):
                        if account_move.get('invoice_date_due') is not False:
                            date_due: datetime = datetime.strptime(account_move.get('invoice_date_due'), "%Y-%m-%d").date()
                            account_move_line ['invoice_date_due'] = date_due
                        else:
                            account_move_line ['invoice_date_due'] = account_move.get('invoice_date_due')
                        account_move_line ['name'] = account_move.get('name')
                        account_move_line ['date_move'] = account_move.get('date')
                        account_move_line ['invoice_payment_state'] = account_move.get('invoice_payment_state')
                        if account_move.get('access_token'):
                            account_move_line["download_url"] = get_download_url(
                            account_move.get('access_token'), account_move.get('id')
                            )
            else:
                account_move_line ['name'] = False
                account_move_line ['date_move'] = False
                account_move_line ['invoice_date_due'] = False
                account_move_line ['invoice_payment_state'] = False
                account_move_line ['download_url'] = False

        for account_move_line in reversed(account_move_line_list):
            balance = balance + (account_move_line.get('debit') - account_move_line.get('credit'))
            account_move_line['balance'] = round(balance, 2)
        paginator = Paginator(account_move_line_list, 20)
        page_number: str = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj
    return context

def save_archive(file, open_ticket_id, contract_id):
    file_name = f"ticket_{open_ticket_id}_contrato_{contract_id}"
    file_extension = os.path.splitext(file.name)[1]
    archive_dict = {
        "name": f"{file_name}",
        "type": "binary",
        "datas": b64encode(file.read()).decode("utf-8"),
        "res_name": f"{file_name}{file_extension}",
        # "store_fname": f"{file_name}",
        "res_model": "helpdesk.ticket",
        "res_id": open_ticket_id,  # Relación con el Ticket
    }

    if file_extension == ".pdf":
        archive_dict["mimetype"] = "application/pdf"
    elif file_extension == ".png":
        archive_dict["mimetype"] = "image/png"
    elif file_extension == ".jpeg":
        archive_dict["mimetype"] = "image/jpeg"

    connection = get_connection()
    archive_model = connection.get_model("ir.attachment")
    archive_model.create(archive_dict)


def save_claim(form_data, open_ticket):
    connection = get_connection()
    ticket_model = connection.get_model("helpdesk.ticket")
    now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    name = form_data.get("name")
    phone_number = form_data.get("phone_number")
    email = form_data.get("email")
    form_description = form_data.get("description")
    client_id = form_data.get("partner_id")
    files = form_data.get("files")
    contract_id = form_data.get("contract_id")
    category_id = form_data.get("category_id")
    open_ticket_id = form_data.get("open_ticket_id")
    open_ticket_description = False

    if open_ticket:
        open_ticket_description = open_ticket["portal_description"]
    description = f"Fecha: {now} <br> Nombre: {name} <br> Número de teléfono: {phone_number} <br> Email: {email} <br> Reclamo: {form_description} <br>"

    if not open_ticket_id:
        ticket_model.create(
            {
                "partner_id": client_id,
                "suscripcion_id": contract_id,
                "name": "Reclamo o solicitud web",
                "description": "-",
                "category_id": category_id,
                "create_uid": 27,
                "portal_description": description,
            }
        )
    else:
        if open_ticket_description:
            description = f"{open_ticket_description} <br> Fecha: {now} <br> {form_description} <br>"
        ticket_model.write(open_ticket_id, {"portal_description": description})

    if files:
        if "files" in files:
            file = files["files"]
            save_archive(file, open_ticket_id, contract_id)
        if "files_second" in files:
            file = files["files_second"]
            save_archive(file, open_ticket_id, contract_id)


def save_recovery(form_data):
    connection = get_connection()
    ticket_model = connection.get_model("helpdesk.ticket")
    now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    dni = form_data.get("dni_recovery")
    contract = form_data.get("client_id")
    name = form_data.get("name_recovery")
    phone = form_data.get("phone_recovery")
    email = form_data.get("email_recovery")
    description = f"<p> Fecha: {now} <br> {dni} <br> {contract} <br> {name} <br> {phone} <br> {email} <br> </p>"
    ticket_model.create(
        {
            "name": "Solicitud de actualización de DNI o CUIT",
            "description": "-",
            "category_id": 41,
            "create_uid": 27,
            "portal_description": description,
        }
    )
