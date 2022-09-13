import json
import werkzeug
from odoo.addons.employee_portal_service.controller.main import EmployeePortal
from odoo import http, _
from odoo.http import request
import base64


class EmployeeProfile(EmployeePortal):

    @http.route('/portal/employee-profile', type='http', auth="user", website=True)
    def my_employee_profile(self, **kwargs):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if not employee:
            return werkzeug.utils.redirect("/portal/home")
        return request.render('employee_portal_service.employee_profile_page',
                              qcontext={
                                  'employee': employee,
                                  'has_employee': True,
                                  'display_button': True
                              })
