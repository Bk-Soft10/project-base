import json
import werkzeug
from odoo.addons.employee_portal_service.controllers.main import EmployeePortal
from odoo import http, _
from odoo.http import request
import base64


class EmployeeContract(EmployeePortal):

    @http.route('/portal/employee-contract', type='http', auth="user", website=True)
    def all_employee_contract(self, **kwargs):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if employee:
            contract_ids = request.env['hr.contract'].sudo().search([('employee_id.id', '=', employee.id)])
        if not employee:
            return werkzeug.utils.redirect("/portal/home")
        return request.render('employee_portal_service.employee_contracts_page',
                              qcontext={'contract_ids': contract_ids,
                                        'employee': employee,
                                        'has_employee': True,
                                        })

    @http.route('/portal/employee-contract/<contract_id>', type='http', auth="user", website=True)
    def details_contract(self, contract_id):
        if not contract_id:
            contract_id = 0
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        contract_row = request.env['hr.contract'].sudo().browse(int(contract_id))
        return request.render('employee_portal_service.view_contract_page',
                              qcontext={
                                  'contract_id': contract_row,
                                  'employee': employee,
                                  'has_employee': True,
                              })
