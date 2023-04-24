import os.path
import re
from base64 import b64encode
from datetime import datetime

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

    return client_data


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


# def valid_change_speed_open(tickets):
#     if tickets is not False:
#         for ticket in tickets:
#             if ticket["category_id"][0] == 45:
#                 cleanr = re.compile("<.*?>")
#                 if ticket["portal_description"] is not False:
#                     ticket["portal_description"] = re.sub(
#                         cleanr, "", ticket["portal_description"]
#                     )
#                 return ticket

#     return False


def format_ticket_description(ticket):
    unformatted_string = re.compile("<.*?>")
    if ticket.get("portal_description"):
        ticket["portal_description"] = re.sub(
            unformatted_string, "", ticket["portal_description"]
        )
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


def fetch_initial_balance(client_id):
    connection = get_connection()
    account_movement_model = connection.get_model("account.move.line")
    initial_balance = account_movement_model.search_read(
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
    )[-1]
    return initial_balance


def save_claim(form_data):
    connection = get_connection()
    ticket_model = connection.get_model("helpdesk.ticket")
    archive_model = connection.get_model("ir.attachment")
    now = datetime.now().strftime("%m/%d/%Y  %H:%M:%S")

    phone_number = form_data.get("phone_number")
    email = form_data.get("email")
    form_description = form_data.get("description")
    client_id = form_data.get("partner_id")
    files = form_data.get("files")
    contract_id = form_data.get("contract_id")
    category_id = form_data.get("category_id")
    open_ticket_id = form_data.get("open_ticket_id")
    open_ticket_description = form_data.get("portal_description")

    description = f"Fecha: {now} <br>Phone number: {phone_number} <br>Email: {email} <br>Descripción: {form_description}"

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
            description = f"{open_ticket_description} <br>Fecha: {now} <br>Descripción: {form_description}"
        ticket_model.write(open_ticket_id, {"portal_description": description})

    if files:
        file_name = f"ticket_{client_id}"
        file_extension = os.path.splitext(files)[1]

        archive_dict = {
            "name": f"{file_name}{file_extension}",
            "type": "binary",
            "datas": b64encode(files.read()).decode("utf-8"),
            "res_name": contract_id,
            "store_fname": contract_id,
            "res_model": "helpdesk.ticket",
            "res_id": contract_id,  # Relación con el Ticket
        }

        if file_extension == ".pdf":
            archive_dict["mimetype"] = "application/pdf"
        elif file_extension == ".png":
            archive_dict["mimetype"] = "image/png"
        elif file_extension == ".jpeg":
            archive_dict["mimetype"] = "image/jpeg"

        archive_model.create(archive_dict)
