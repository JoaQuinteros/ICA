from base64 import b64encode
from typing import Any, Dict, List

import odoolib
import requests
from decouple import config
from django.core.exceptions import ValidationError
import re
from django.conf import settings
import os.path
from datetime import datetime

def get_connection():
    try:
        connection = odoolib.get_connection(
            hostname=config("ODOO_DB_HOSTNAME"),
            database=config("ODOO_DB_NAME"),
            login=config("ODOO_DB_LOGIN"),
            password=config("ODOO_DB_PASSWORD"),
            port=443,
            protocol="jsonrpcs"
        )
        return connection
    except (requests.exceptions.ConnectionError, odoolib.main.AuthenticationError, odoolib.main.JsonRPCException):
        raise ValidationError("No pudimos procesar tu pedido.")
    
    
def get_client_data(dni: str) -> Dict[str, Any]:
    connection = get_connection()
    client_model = connection.get_model('res.partner')
    client_data: List[Dict[str, Any]] = client_model.search_read([('vat', '=', dni)], ['id','internal_code','name','email','vat','contract_ids','credit'])
    if client_data:
        return client_data[0]
    return False


def get_contract_data(id: str) -> Dict[str, Any]:
    connection = get_connection()
    contract_model = connection.get_model('contract.contract')
    contract_data: List[Dict[str, Any]] = contract_model.search_read([('id', '=', id)], ['id','active','is_terminated','domicilio','localidad','latitud','longitud','ssid_id','sistema_autonomo_id','servicio_suspendido','ssid_state'])
    if contract_data:
        return contract_data[0]
    return False

def get_client_tickets(id: str) -> Dict[str, Any]:
    connection = get_connection()
    ticket_model = connection.get_model('helpdesk.ticket')
    ticket_closed_model = connection.get_model('helpdesk.ticket.stage')
    stages_closed = get_stages_closed()
    contract_data: List[Dict[str, Any]] = ticket_model.search_read([('suscripcion_id', '=', id),('stage_id','!=', stages_closed),('create_uid','=', 27)], ['id','number','portal_description','stage_id','partner_id','stage_id','category_id','suscripcion_id'])
    #
    if contract_data:
        print("Se encontro")
        print(contract_data)
        return contract_data
    return False

def get_stages_closed():
    connection = get_connection()
    stages_closed = []
    ticket_closed_model = connection.get_model('helpdesk.ticket.stage')
    stage_ticket = ticket_closed_model.search_read([('closed','=',True)]) # obtain the list of stages of tickets that belongs to tickets that are closed
    for ts in stage_ticket:
        stages_closed.append(ts.get('id'))
    return stages_closed

def valid_change_speed_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 45:
                cleanr = re.compile('<.*?>')
                if ticket['portal_description'] is not False:
                    ticket['portal_description'] = re.sub(cleanr, '',ticket['portal_description'])
                return ticket
    return False

def valid_admin_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 41:
                cleanr = re.compile('<.*?>')
                if ticket['portal_description'] is not False:
                    ticket['portal_description'] = re.sub(cleanr, '',ticket['portal_description'])
                return ticket
    return False

def valid_service_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 34:
                cleanr = re.compile('<.*?>')
                if ticket['portal_description'] is not False:
                    ticket['portal_description'] = re.sub(cleanr, '',ticket['portal_description'])
                return ticket
    return False

def valid_unsuscribe_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 56:
                cleanr = re.compile('<.*?>')
                if ticket['portal_description'] is not False:
                    ticket['portal_description'] = re.sub(cleanr, '',ticket['portal_description'])
                return ticket
    return False

def valid_change_adress_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 36:
                cleanr = re.compile('<.*?>')
                if ticket['portal_description'] is not False:
                    ticket['portal_description'] = re.sub(cleanr, '',ticket['portal_description'])
                return ticket
    return False


def get_account_data(partner_id: str) -> List[Dict[str, Any]]:
    connection = get_connection()
    account_model = connection.get_model("account.move")
    account_data: List[Dict[str, Any]] = account_model.search_read(
        [("partner_id", "=", partner_id),("state","=","posted")],
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
    if account_data:
        return account_data
    return False

def get_account_data_move(id) -> List[Dict[str, Any]]:
    connection = get_connection()
    account_model = connection.get_model("account.move")
    account_data: List[Dict[str, Any]] = account_model.search_read(
        [("id", "=", id),("state","=","posted")],
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
    if account_data:
        return account_data
    return False

def get_account_line_data(partner_id: str) -> List[Dict[str, Any]]:
    connection = get_connection()
    account_line_model = connection.get_model("account.move.line")
    account_line_list: List[Dict[str, Any]] = account_line_model.search_read(
        [("partner_id", "=", partner_id),('account_id', '=' ,6),('parent_state', '=' ,"posted")],
        [
            # "move_id",
            #"move_name",
            "ref",
            # "partner_id",
            "date",
            # "date_maturity",
            # "debit",
            # "credit",
             "move_id",
             "debit",
             "credit",
        ],
    )#VALIDAR con tipo de move osea si es RE y NC no sino con el tipo
    if account_line_list:
        for account_move_line in account_line_list:
            if account_move_line.get('move_id') is not False:
                account_move = list(get_account_data_move(account_move_line.get('move_id')[0]))[0]
                if account_move.get('invoice_date_due') is not False:
                    date_due : datetime = datetime.strptime(account_move.get('invoice_date_due'), "%Y-%m-%d").date()
                    account_move_line ['invoice_date_due'] = date_due
                else:
                    account_move_line ['invoice_date_due'] = account_move.get('invoice_date_due')
                account_move_line ['name'] = account_move.get('name')
                account_move_line ['date_move'] = account_move.get('date')
                account_move_line ['invoice_payment_state'] = account_move.get('invoice_payment_state')
                account_move_line ['access_token'] = account_move.get('access_token')
            else:
                account_move_line ['name'] = False
                account_move_line ['date_move'] = False
                account_move_line ['invoice_date_due'] = False
                account_move_line ['invoice_payment_state'] = False
                account_move_line ['access_token'] = False
        return account_line_list
    return False

def save_claim(dni, id, category, phone_number, email, description, files):
    connection = get_connection()
    now = datetime.now().strftime("%m/%d/%Y  %H:%M:%S")
    description = 'Fecha: ' + now + ' <br> phone number: ' + phone_number + ' <br> email: ' + email + ' <br> descripcion: ' + description
    archive_model = connection.get_model('ir.attachment')
    ticket_model = connection.get_model('helpdesk.ticket')
    client_data: Dict[str, Any] = get_client_data(dni)
    ticket_model.create({'partner_id':client_data.get('id'),'suscripcion_id':id,'name':'Reclamo o solicitud web','description':'-','category_id':category,'create_uid':27,'portal_description':description})
    if files:
        if files.size < int(settings.MAX_UPLOAD_SIZE):
            name, type_file = os.path.splitext(files)
            name_file = 'ticket_' + str(client_data.get('id'))
            if type_file is '.pdf':
                archive_model.create({'name':name_file,'type':'binary','datas':files,'res_name':id,'store_fname':id,'res_model':'helpdesk.ticket','res_id':id,'mimetype':'application/x-pdf'})
            elif type_file is '.png':
                archive_model.create({'name':name_file,'type':'binary','datas':files,'res_name':id,'store_fname':id,'res_model':'helpdesk.ticket','res_id':id,'mimetype':'application/x-pdf'})
            elif type_file is '.jpeg':
                archive_model.create({'name':name_file,'type':'binary','datas':files,'res_name':id,'store_fname':id,'res_model':'helpdesk.ticket','res_id':id,'mimetype':'image/jpeg'})


def add_info_claim(dni, id, id_ticket, ticket_description, description, files):
    connection = get_connection()
    ticket_model = connection.get_model('helpdesk.ticket')
    archive_model = connection.get_model('ir.attachment')
    client_data: Dict[str, Any] = get_client_data(dni)
    now = datetime.now().strftime("%m/%d/%Y  %H:%M:%S")
    if ticket_description != 'False':
        description = ticket_description + '<br> Fecha: ' + now + ' <br> descripcion: ' + description
    else:
        description = 'Fecha: ' + now + ' <br> descripcion: ' + description
    id_ticket_int = int(id_ticket)
    ticket_model.write(id_ticket_int,{'portal_description':description})
    if files:
        if files.size < int(settings.MAX_UPLOAD_SIZE):
            name, type_file = os.path.splitext(files.name)
            name_file = 'ticket_' + str(id_ticket)
            res_name = str(id_ticket) + ' - ' + str(client_data.get('name'))
            if type_file == '.pdf':
                archive_model.create({'name':name_file,'type':'binary','datas':b64encode(files.read()).decode('utf-8'),'res_name':name_file +'.pdf','res_model':'helpdesk.ticket','res_id':id_ticket,'mimetype':'application/x-pdf'})
            elif type_file == '.png':
                archive_model.create({'name':name_file,'type':'binary','datas':b64encode(files.read()).decode('utf-8'),'res_name':name_file +'.png','res_model':'helpdesk.ticket','res_id':id_ticket,'mimetype':'image/png'})
            elif type_file == '.jpeg':
                archive_model.create({'name':name_file,'type':'binary','datas':b64encode(files.read()).decode('utf-8'),'res_name':name_file +'.jpeg','res_model':'helpdesk.ticket','res_id':id_ticket,'mimetype':'image/jpeg'})