import json
import werkzeug
from odoo.addons.employee_portal_service.controller.main import EmployeePortal
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo import http, _
from odoo.http import request
from collections import OrderedDict
import base64


class EmployeeExpense(EmployeePortal):

    @http.route(['/portal/employee-expense', '/portal/employee-expense/page/<int:page>'], type='http', auth="user", website=True)
    def all_employee_expense(self, page=1, sortby=None, filterby=None, **kw):
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
            'draft': {'label': _('To Submit'), 'domain': [('state', '=', 'draft')]},
            'reported': {'label': _('Submitted'), 'domain': [('state', '=', 'reported')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approved')]},
            'done': {'label': _('Paid'), 'domain': [('state', '=', 'done')]},
            'refused': {'label': _('Refused'), 'domain': [('state', '=', 'refused')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if employee:
            domain = [('employee_id.user_id', '=', request.env.user.id)]
            domain += searchbar_filters[filterby]['domain']
            record_len = request.env['hr.expense'].sudo().search_count([('employee_id.user_id', '=', request.env.user.id)]) or 0
            pager = portal_pager(
                url="/portal/employee-expense",
                total=record_len,
                page=page,
                step=self._items_per_page
            )
            expense_ids = request.env['hr.expense'].sudo().search(
                domain,
                order=order,
                limit=self._items_per_page,
                offset=pager['offset']
            )
        if not employee:
            return werkzeug.utils.redirect("/portal/home")
        res_dict = {
            'expense_ids': expense_ids,
            'employee': employee,
            'has_employee': True,
            'page_name': 'expenses_list_page',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/portal/employee-expense',
        }
        return request.render('employee_portal_service.employee_expenses_list_page',
                              qcontext=res_dict)

    @http.route('/portal/employee-expense/<expense_id>', type='http', auth="user", website=True)
    def details_expense(self, expense_id):
        if not expense_id:
            expense_id = 0
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        expense_row = request.env['hr.expense'].sudo().browse(int(expense_id))
        return request.render('employee_portal_service.view_expense_page',
                              qcontext={
                                  'expense_id': expense_row,
                                  'employee': employee,
                                  'has_employee': True,
                              })
