import os.path
import re
from base64 import b64encode
from datetime import datetime

import odoolib
import requests
from decouple import config
from django.conf import settings
from django.core.cache import cache
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


async def fetch_all_data(dni):
    connection = get_connection()

    client = fetch_client_data(dni, connection)
    cache.set(f"{dni}", client)

    if client == "Not found":
        return

    contracts_list = fetch_contracts_list(client.get("contract_ids"), connection)

    if not contracts_list:
        return

    client["contracts_list"] = contracts_list
    client["initial_balance"] = fetch_initial_balance(dni, connection)
    client["account_movements"] = fetch_account_movements(dni, connection)
    cache.set(f"{dni}", client)


# region asd


def fetch_client_data(dni, connection):
    client_model = connection.get_model("res.partner")
    client_data = client_model.search_read(
        [("vat", "=", dni)],
        ["id", "internal_code", "name", "email", "vat", "contract_ids", "credit"],
    )[0]

    if client_data:
        return client_data

    return "Not found"


def fetch_contracts_list(contract_ids, connection):
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


def valid_change_speed_open(tickets):
    if tickets is not False:
        for ticket in tickets:
            if ticket["category_id"][0] == 45:
                cleanr = re.compile("<.*?>")
                if ticket["portal_description"] is not False:
                    ticket["portal_description"] = re.sub(
                        cleanr, "", ticket["portal_description"]
                    )
                return ticket

    return False


def valid_admin_open(ticket_list):
    for ticket in ticket_list:
        if ticket.get("category_id")[0] == 41:
            cleanr = re.compile("<.*?>")
            if ticket.get("portal_description"):
                ticket["portal_description"] = re.sub(
                    cleanr, "", ticket["portal_description"]
                )
            return ticket
    return False


def valid_service_open(tickets):
    if tickets is not False:
        for ticket in tickets:
            if ticket["category_id"][0] == 34:
                cleanr = re.compile("<.*?>")
                if ticket["portal_description"] is not False:
                    ticket["portal_description"] = re.sub(
                        cleanr, "", ticket["portal_description"]
                    )
                return ticket
    return False


def valid_unsuscribe_open(tickets):
    if tickets is not False:
        for ticket in tickets:
            if ticket["category_id"][0] == 56:
                cleanr = re.compile("<.*?>")
                if ticket["portal_description"] is not False:
                    ticket["portal_description"] = re.sub(
                        cleanr, "", ticket["portal_description"]
                    )
                return ticket
    return False


def valid_change_adress_open(tickets):
    if tickets is not False:
        for ticket in tickets:
            if ticket["category_id"][0] == 36:
                cleanr = re.compile("<.*?>")
                if ticket["portal_description"] is not False:
                    ticket["portal_description"] = re.sub(
                        cleanr, "", ticket["portal_description"]
                    )
                return ticket
    return False


# endregion


def fetch_account_movements(partner_id, connection):
    account_model = connection.get_model("account.move")
    account_movements_list = account_model.search_read(
        [("partner_id", "=", partner_id), ("state", "=", "posted")],
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


def fetch_initial_balance(partner_id, connection):
    account_movement_model = connection.get_model("account.move.line")
    initial_balance = account_movement_model.search_read(
        [
            ("partner_id", "=", partner_id),
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
    archive_model = connection.get_model("ir.attachment")
    ticket_model = connection.get_model("helpdesk.ticket")
    now = datetime.now().strftime("%m/%d/%Y  %H:%M:%S")
    description = f'Fecha: {now}<br>Phone number: {form_data.get("phone_number")}<br>Email: {form_data.get("email")}<br>Descripción: {form_data.get("description")}'
    id = form_data.get("partner_id")
    files = form_data.get("files")

    ticket_model.create(
        {
            "partner_id": id,
            "suscripcion_id": form_data.get("contract_id"),
            "name": "Reclamo o solicitud web",
            "description": "-",
            "category_id": form_data.get("category_id"),
            "create_uid": 27,
            "portal_description": description,
        }
    )

    if files:
        file_name = f"ticket_{id}"
        file_extension = os.path.splitext(files)[1]

        archive_dict = {
            "name": file_name,
            "type": "binary",
            "datas": files,
            "res_name": id,
            "store_fname": id,
            "res_model": "helpdesk.ticket",
            "res_id": id,
        }

        if file_extension == ".pdf":
            archive_dict["mimetype"] = "application/x-pdf"
        elif file_extension == ".png":
            archive_dict["mimetype"] = "image/png"
        elif file_extension == ".jpeg":
            archive_dict["mimetype"] = "image/jpeg"

        archive_model.create(archive_dict)


def add_info_claim(dni, id, id_ticket, ticket_description, description, files):
    connection = get_connection()
    ticket_model = connection.get_model("helpdesk.ticket")
    archive_model = connection.get_model("ir.attachment")
    now = datetime.now().strftime("%m/%d/%Y  %H:%M:%S")
    client_data = fetch_client_data(dni)
    if ticket_description != "False":
        description = (
            ticket_description
            + "<br> Fecha: "
            + now
            + " <br> descripcion: "
            + description
        )
    else:
        description = "Fecha: " + now + " <br> descripcion: " + description
    id_ticket_int = int(id_ticket)
    ticket_model.write(id_ticket_int, {"portal_description": description})
    if files:
        if files.size < int(settings.MAX_UPLOAD_SIZE):
            name, type_file = os.path.splitext(files.name)
            name_file = "ticket_" + str(id_ticket)
            res_name = str(id_ticket) + " - " + str(client_data.get("name"))
            if type_file == ".pdf":
                archive_model.create(
                    {
                        "name": name_file,
                        "type": "binary",
                        "datas": b64encode(files.read()).decode("utf-8"),
                        "res_name": name_file + ".pdf",
                        "res_model": "helpdesk.ticket",
                        "res_id": id_ticket,
                        "mimetype": "application/x-pdf",
                    }
                )
            elif type_file == ".png":
                archive_model.create(
                    {
                        "name": name_file,
                        "type": "binary",
                        "datas": b64encode(files.read()).decode("utf-8"),
                        "res_name": name_file + ".png",
                        "res_model": "helpdesk.ticket",
                        "res_id": id_ticket,
                        "mimetype": "image/png",
                    }
                )
            elif type_file == ".jpeg":
                archive_model.create(
                    {
                        "name": name_file,
                        "type": "binary",
                        "datas": b64encode(files.read()).decode("utf-8"),
                        "res_name": name_file + ".jpeg",
                        "res_model": "helpdesk.ticket",
                        "res_id": id_ticket,
                        "mimetype": "image/jpeg",
                    }
                )
