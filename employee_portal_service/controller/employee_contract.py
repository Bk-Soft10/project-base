import json
import werkzeug
from odoo.addons.employee_portal_service.controller.main import EmployeePortal
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo import http, _
from odoo.http import request
from collections import OrderedDict
import base64


class EmployeeContract(EmployeePortal):

    @http.route(['/portal/employee-contract', '/portal/employee-contract/page/<int:page>'], type='http', auth="user", website=True)
    def all_employee_contract(self, page=1, sortby=None, filterby=None, **kw):
        record_len = 0
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'not in', ['xxx'])]},
            'draft': {'label': _('New'), 'domain': [('state', '=', 'draft')]},
            'open': {'label': _('Running'), 'domain': [('state', '=', 'open')]},
            'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
            'close': {'label': _('Expired'), 'domain': [('state', '=', 'close')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if employee:
            domain = [('employee_id.user_id', '=', request.env.user.id)]
            domain += searchbar_filters[filterby]['domain']
            record_len = request.env['hr.contract'].sudo().search_count([('employee_id.user_id', '=', request.env.user.id)]) or 0
            pager = portal_pager(
                url="/portal/employee-contract",
                total=record_len,
                page=page,
                step=self._items_per_page
            )
            contract_ids = request.env['hr.contract'].sudo().search(
                domain,
                order=order,
                limit=self._items_per_page,
                offset=pager['offset']
            )
        if not employee:
            return werkzeug.utils.redirect("/portal/home")
        res_dict = {
            'contract_ids': contract_ids,
            'employee': employee,
            'has_employee': True,
            'page_name': 'contracts_list_page',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/portal/employee-contract',
        }
        return request.render('employee_portal_service.employee_contracts_list_page',
                              qcontext=res_dict)

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
