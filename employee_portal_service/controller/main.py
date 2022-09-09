# -*- encoding: utf-8 -*-

import os
import base64
import odoo
import json
import werkzeug.utils
import odoo.modules.registry
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home as HomeOld, ensure_db
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as AuthSignupHomeOld
import datetime
import logging

_logger = logging.getLogger(__name__)
from odoo.addons.auth_signup.models.res_users import SignupError

INVALID_CREDENTIALS = {
    'code': 100,
    'message': 'Invalid Credentials',
}
DATA_NOT_FOUND = {
    'code': 101,
    'message': 'Data not available',
}
INVALID_REQUEST = {
    'code': 102,
    'message': 'Invalid Request',
}
import json


def response_ok(result):
    response = {
        'code': 200,
        'result': result,
    }
    return json.dumps(response)


def response_nodata():
    return json.dumps(DATA_NOT_FOUND)


def response_invalidcredentials():
    return json.dumps(INVALID_CREDENTIALS)


def response_invalidrequest():
    return json.dumps(INVALID_REQUEST)


try:
    import base64
except ImportError:
    base64 = None

PPG = 10  # Per Page
PPR = 4  # Per Row

# class Home(HomeOld):
#
#     @http.route()
#     def web_login(self, redirect=None, **kw):
#         return super(Home, self).web_login('/portal/home', **kw)


class EmployeePortal(http.Controller):

    @http.route('/portal/home', auth="user", website=True)
    def page_portal_index(self, **kw):
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        return request.render("employee_portal_service.portal_home", {'employee': employee_id})
