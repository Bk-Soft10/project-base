import ast
import datetime
import json
import logging

import werkzeug.wrappers

_logger = logging.getLogger(__name__)


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str(o)

def return_response(msg, code=200, data=[]):
    response = {
        'code': code,
        'msg': msg,
        'data': data or [],
    }
    return response

def valid_response(data, status=200):
    """Valid Response
    This will be return when the http request was successfully processed."""
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}
    response_v = json.dumps(data, default=default)
    # response_v = data
    return werkzeug.wrappers.Response(
        status=status, content_type="application/json; charset=utf-8", response=response_v,
    )


def invalid_response(typ, message=None, status=401):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    # return json.dumps({})
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {"type": typ, "message": str(message) if str(message) else "wrong arguments (missing validation)",},
            default=datetime.datetime.isoformat,
        ),
    )

def record_fields_dict(obj, list_fields=[]):
    def _getattrstring(obj, field_str):
        field_value = obj[field_str]
        if obj._fields[field_str].type == 'many2one':
            field_value = field_value.id
        if obj._fields[field_str].type in ['many2many', 'one2many']:
            field_value = field_value.ids
        return field_value

    values = {}
    if not list_fields:
        list_fields = obj._fields
    for field in list_fields:
        value_field = _getattrstring(obj, field)
        values[field] = value_field
    return values


def extract_arguments(limit="80", offset=0, order="id", domain="", fields=[]):
    """Parse additional data  sent along request."""
    limit = int(limit)
    expresions = []
    if domain:
        expresions = [tuple(preg.replace(":", ",").split(",")) for preg in domain.split(",")]
        expresions = json.dumps(expresions)
        expresions = json.loads(expresions, parse_int=True)
    if fields:
        fields = fields.split(",")

    if offset:
        offset = int(offset)
    return [expresions, fields, offset, limit, order]
