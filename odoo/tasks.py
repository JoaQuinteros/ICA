from typing import Any, Dict, List

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
    if contract_data:
        print("Se encontro")
        print(contract_data)
        return contract_data
    return False
    #for c in contract_data:
    #    print(c)

# def valid_change_speed_open(tickets: Dict[str, Any], claim_ticket) -> Dict[str, Any]:
#     if tickets is not False:
#         for ticket in tickets:
#             if ticket['category_id'][0] == 45:
#                 print(ticket['category_id'][0])
#                 print(ticket)
#                 return ticket
#     return False

def valid_change_speed_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 45:
                print(ticket['category_id'][0])
                print(ticket)
                return ticket
    return False

def valid_admin_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 41:
                print(ticket['category_id'][0])
                print(ticket)
                return ticket
    return False

def valid_service_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 34:
                print(ticket['category_id'][0])
                print(ticket)
                return ticket
    return False

def valid_unsuscribe_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 56:
                print(ticket['category_id'][0])
                print(ticket)
                return ticket
    return False

def valid_change_adress_open(tickets: Dict[str, Any]) -> Dict[str, Any]:
    if tickets is not False:
        for ticket in tickets:
            if ticket['category_id'][0] == 36:
                print(ticket['category_id'][0])
                print(ticket)
                return ticket
    return False