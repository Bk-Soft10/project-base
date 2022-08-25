# -*- encoding: utf-8 -*-

from odoo.http import request
from odoo import http
import json
import logging
from datetime import datetime
from dateutil import relativedelta
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo.addons.web.controllers.main import db_monodb, ensure_db, set_cookie_and_redirect, login_and_redirect
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval
import functools
import werkzeug.wrappers

from odoo.addons.app_api.common import invalid_response, valid_response, return_response, record_fields_dict
from odoo.exceptions import AccessDenied, AccessError

try:
    import base64
except ImportError:
    base64 = None

_logger = logging.getLogger(__name__)


class APIController(http.Controller):

    @http.route('/api/<model_id>/<rec_id>/<res_func>', methods=['POST'], type='http', auth="user", csrf=False)
    def api_run_method(self, model_id, rec_id, res_func):
        try:
            # data = json.loads(request.httprequest.data)
            record_id = request.env[model_id].sudo().search([('id', '=', int(rec_id or 0))])
            if record_id and res_func:
                getattr(record_id, res_func)()
                response = {
                    'code': 200,
                    'msg': 'Success',
                    'id': record_id.id or False
                }
                return response
            else:
                response = {
                    'code': 101,
                    'msg': 'Not Found'
                }
                return response

        except Exception as ex:
            _logger.exception(ex)
            response = {
                'code': 102,
                'msg': 'Invalid Request',
                'ex': str(ex)
            }
            return response

    def _perpare_run_function_vals(self, post):
        if not post:
            post = json.loads(request.httprequest.data)
        params = ["model_name", "record_id", "function_name", "dict_val"]
        vals = {key: post.get(key) for key in params if post.get(key)}
        model_name, record_id, function_name, dict_val = (
            vals.get("model_name") if 'model_name' in vals else False,
            vals.get("record_id") if 'record_id' in vals else False,
            vals.get("function_name") if 'function_name' in vals else False,
            vals.get("dict_val") if 'dict_val' in vals else False,
        )
        _parms_includes_in_body = all([model_name, function_name])
        if not _parms_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            vals = {key: headers.get(key) for key in params if headers.get(key)}
            model_name, record_id, function_name, dict_val = (
                vals.get("model_name") if 'model_name' in vals else False,
                vals.get("record_id") if 'record_id' in vals else False,
                vals.get("function_name") if 'function_name' in vals else False,
                vals.get("dict_val") if 'dict_val' in vals else False,
            )
            _parms_includes_in_headers = all([model_name, function_name])
            if not _parms_includes_in_headers:
                # Empty 'model_name' or 'record_id' or 'function_name:
                return_response(msg='either of the following are missing [model_name, record_id, function_name]', code=403, data=[])
                # return invalid_response(
                #     "missing error", "either of the following are missing [model_name, record_id, function_name]", 403,
                # )
        return vals

    @http.route('/api/run_function', methods=['POST'], type='json', auth='user', csrf=False)
    def run_function(self, **post):
        try:
            vals = self._perpare_run_function_vals(post) or {}
            model_name, record_id, function_name, dict_val = (
                vals.get("model_name") if 'model_name' in vals else False,
                vals.get("record_id") if 'record_id' in vals else False,
                vals.get("function_name") if 'function_name' in vals else False,
                vals.get("dict_val") if 'dict_val' in vals else False,
            )
            if request.jsonrequest and model_name and function_name:
                record_set = False
                resource_model = request.env[model_name]
                if dict_val and function_name in ['create']:
                    record_set = getattr(resource_model, function_name)(dict_val)
                    return return_response(msg='Successfully', code=200,
                                           data=[{"record_id": record_set.id or 0, "model_name": model_name}])
                elif record_id:
                    record_set = resource_model.sudo().browse([int(record_id or 0)])
                    if record_set and function_name:
                        if dict_val:
                            getattr(record_set, function_name)(dict_val)
                        else:
                            getattr(record_set, function_name)()
                        return return_response(msg='Successfully', code=200,
                                               data=[{"record_id": record_set.id or 0, "model_name": model_name}])
                else:
                    return return_response(msg='Cannot Find Record Set', code=403, data=[])
            else:
                return return_response(msg='Missing Values', code=403, data=[])

        except Exception as ex:
            return return_response(msg=ex, code=403, data=[])

    def _perpare_one_recordset_values(self, post):
        if not post:
            post = json.loads(request.httprequest.data)
        params = ["model_name", "record_id", "list_fields"]
        vals = {key: post.get(key) for key in params if post.get(key)}
        model_name, record_id, list_fields = (
            vals.get("model_name") if 'model_name' in vals else False,
            vals.get("record_id") if 'record_id' in vals else False,
            vals.get("list_fields") if 'list_fields' in vals else False,
        )
        _parms_includes_in_body = all([model_name, record_id])
        if not _parms_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            vals = {key: headers.get(key) for key in params if headers.get(key)}
            model_name, record_id, list_fields = (
                vals.get("model_name") if 'model_name' in vals else False,
                vals.get("record_id") if 'record_id' in vals else False,
                vals.get("list_fields") if 'list_fields' in vals else False,
            )
            _parms_includes_in_headers = all([model_name, record_id])
            if not _parms_includes_in_headers:
                # Empty 'model_name' or 'record_id' or 'domain:
                return_response(msg='either of the following are missing [model_name, record_id]', code=403, data=[])
        return vals

    @http.route("/api/get_fields_value/one", methods=["GET"], type="json", auth="user", csrf=False)
    def get_one_recordset_values(self, **post):
        try:
            vals = self._perpare_one_recordset_values(post) or {}
            model_name, record_id, list_fields = (
                vals.get("model_name") if 'model_name' in vals else False,
                vals.get("record_id") if 'record_id' in vals else False,
                vals.get("list_fields") if 'list_fields' in vals else False,
            )
            if request.jsonrequest and model_name and record_id:
                resource_model = request.env[model_name]
                record_set = resource_model.sudo().browse([int(record_id or 0)])
                if record_set:
                    record_dict = {'id': record_set.id, 'display_name': record_set.display_name}
                    if list_fields:
                        record_dict['fields'] = record_fields_dict(record_set, list_fields)
                    else:
                        record_dict['fields'] = record_fields_dict(record_set)
                    return return_response(msg='Successfully', code=200,
                                           data=[{
                                               "model_name": model_name,
                                               "record_id": record_set.id or 0,
                                               "record_dict": record_dict or {},
                                           }])
                else:
                    return return_response(msg='Cannot Find Record Set', code=403, data=[])
            else:
                return return_response(msg='Missing Values', code=403, data=[])
        except Exception as ex:
            return return_response(msg=ex, code=403, data=[])

    def _perpare_multi_recordset_values(self, post):
        if not post:
            post = json.loads(request.httprequest.data)
        params = ["model_name", "domain", "list_fields"]
        vals = {key: post.get(key) for key in params if post.get(key)}
        model_name, domain, list_fields = (
            vals.get("model_name") if 'model_name' in vals else False,
            vals.get("domain") if 'domain' in vals else False,
            vals.get("list_fields") if 'list_fields' in vals else False,
        )
        _parms_includes_in_body = all([model_name, domain])
        if not _parms_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            vals = {key: headers.get(key) for key in params if headers.get(key)}
            model_name, domain, list_fields = (
                vals.get("model_name") if 'model_name' in vals else False,
                vals.get("domain") if 'domain' in vals else False,
                vals.get("list_fields") if 'list_fields' in vals else False,
            )
            _parms_includes_in_headers = all([model_name, domain])
            if not _parms_includes_in_headers:
                # Empty 'model_name' or 'record_id' or 'domain:
                return_response(msg='either of the following are missing [model_name, record_id, domain]', code=403, data=[])
        return vals

    @http.route("/api/get_fields_value/multi", methods=["GET"], type="json", auth="user", csrf=False)
    def get_multi_recordset_values(self, **post):
        try:
            vals = self._perpare_multi_recordset_values(post) or {}
            model_name, domain, list_fields = (
                vals.get("model_name") if 'model_name' in vals else False,
                vals.get("domain") if 'domain' in vals else False,
                vals.get("list_fields") if 'list_fields' in vals else False,
            )
            if request.jsonrequest and model_name and domain:
                resource_model = request.env[model_name]
                records_set = resource_model.sudo().search(domain)
                if records_set:
                    result_lst = []
                    for record in records_set:
                        record_dict = {'id': record.id, 'display_name': record.display_name}
                        if list_fields:
                            record_dict['fields'] = record_fields_dict(record, list_fields)
                        else:
                            record_dict['fields'] = record_fields_dict(record)
                        result_lst.append(record_dict)
                    return return_response(msg='Successfully', code=200,
                                           data=[{
                                               "model_name": model_name,
                                               "record_ids": records_set.ids or [],
                                               "record_values": result_lst or [],
                                           }])
                else:
                    return return_response(msg='Cannot Find Record Set', code=403, data=[])
            else:
                return return_response(msg='Missing Values', code=403, data=[])


        except Exception as ex:
            return return_response(msg=ex, code=403, data=[])

    def _perpare_get_model_name(self, post):
        if not post:
            post = json.loads(request.httprequest.data)
        model_name = post.get("model_name") if 'model_name' in post else False
        if not model_name:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            model_name = headers.get("model_name") if 'model_name' in headers else False
            if not model_name:
                return_response(msg='either of the following are missing [model_name]', code=403, data=[])
        return model_name

    @http.route("/api/get_fields_list", methods=["GET"], type="json", auth="user", csrf=False)
    def get_fields_list(self, **post):
        try:
            model_name = self._perpare_get_model_name(post) or False
            if request.jsonrequest and model_name:
                resource_model = request.env['ir.model']
                model_id = resource_model.sudo().search([('model', '=', model_name)])
                if model_id:
                    fields_lst = []
                    model_dict = {'id': model_id.id, 'display_name': model_id.display_name}
                    for field_id in model_id.field_id:
                        field_info = {'field_name': field_id.name, 'field_description': field_id.field_description, 'type': field_id.ttype}
                        fields_lst.append(field_info)
                    model_dict['fields'] = fields_lst
                    return return_response(msg='Successfully', code=200,
                                           data=fields_lst)
                else:
                    return return_response(msg='Cannot Find Model', code=403, data=[])
            else:
                return return_response(msg='Missing Values', code=403, data=[])


        except Exception as ex:
            return return_response(msg=ex, code=403, data=[])
