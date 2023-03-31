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
    contract_data: List[Dict[str, Any]] = contract_model.search_read([('id', '=', id)], ['id','active','is_terminated','domicilio','localidad','latitud','longitud','ssid_id','sistema_autonomo_id','servicio_suspendido'])
    if contract_data:
        return contract_data[0]
    return False

def get_client_tickets(id: str) -> Dict[str, Any]:
    connection = get_connection()
    ticket_model = connection.get_model('helpdesk.ticket')
    ticket_closed_model = connection.get_model('helpdesk.ticket.stage')
    stage_ticket = ticket_closed_model.search_read([('closed','=',True)]) # obtain the list of stages of tickets that belongs to tickets that are closed
    stages_closed = []
    for ts in stage_ticket:
        stages_closed.append(ts.get('id'))
    contract_data: List[Dict[str, Any]] = ticket_model.search_read([('suscripcion_id', '=', id),('stage_id','!=', stages_closed)], ['id','number','description','stage_id','partner_id','stage_id','category_id','suscripcion_id'])
    #,('create_uid','=', 27)
    if contract_data:
        print("Se encontro")
        print(contract_data)
        return contract_data
    return False
    #for c in contract_data:
    #    print(c)

def valid_change_speed_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 45:
                cleanr = re.compile('<.*?>')
                ticket['description'] = re.sub(cleanr, '',ticket['description'])
                return ticket
    return False

def valid_admin_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 41:
                cleanr = re.compile('<.*?>')
                ticket['description'] = re.sub(cleanr, '',ticket['description'])
                return ticket
    return False

def valid_service_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 34:
                cleanr = re.compile('<.*?>')
                ticket['description'] = re.sub(cleanr, '',ticket['description'])
                return ticket
    return False

def valid_unsuscribe_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 56:
                cleanr = re.compile('<.*?>')
                ticket['description'] = re.sub(cleanr, '',ticket['description'])
                return ticket
    return False

def valid_change_adress_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 36:
                cleanr = re.compile('<.*?>')
                ticket['description'] = re.sub(cleanr, '',ticket['description'])
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
    )
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

def save_claim(dni, id, phone_number, email, description, files):
    connection = get_connection()
    archive_model = connection.get_model('ir.attachment')
    #print(files.size)
    #print(os.path.getsize(files.size))
    #if files.size < int(settings.MAX_UPLOAD_SIZE):
    #    print(files)
        #name, type = os.path.splitext(files)
        # if type is '.pdf':
        #     archive_model.create({'name':id,'type':'binary','datas':file,'res_name':id,'store_fname':id,'res_model':'helpdesk.ticket','res_id':id,'mimetype':'application/x-pdf'})
        # elif type is '.png':
        #     archive_model.create({'name':id,'type':'binary','datas':file,'res_name':id,'store_fname':id,'res_model':'helpdesk.ticket','res_id':id,'mimetype':'application/x-pdf'})
        # elif type is '.jpeg':
        #     archive_model.create({'name':id,'type':'binary','datas':file,'res_name':id,'store_fname':id,'res_model':'helpdesk.ticket','res_id':id,'mimetype':'image/jpeg'})


def add_info_claim(dni, id, description):
   connection = get_connection()
   ticket_model = connection.get_model('helpdesk.ticket') 
   #ticket_model.create({'id':id,'description':description})