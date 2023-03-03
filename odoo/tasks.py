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

