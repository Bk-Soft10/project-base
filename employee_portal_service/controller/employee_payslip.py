import json
import werkzeug
from odoo.addons.employee_portal_service.controller.main import EmployeePortal
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo import http, _
from odoo.http import request
from collections import OrderedDict
import base64


class EmployeePayslip(EmployeePortal):

    @http.route(['/portal/employee-payslip', '/portal/employee-payslip/page/<int:page>'], type='http', auth="user", website=True)
    def all_employee_payslip(self, page=1, sortby=None, filterby=None, **kw):
        record_len = 0
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'not in', ['xxx'])]},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
            'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
            'credit_note': {'label': _('Credit Note'), 'domain': [('credit_note', '=', True)]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if employee:
            domain = [('employee_id.user_id', '=', request.env.user.id)]
            domain += searchbar_filters[filterby]['domain']
            record_len = request.env['hr.payslip'].sudo().search_count([('employee_id.user_id', '=', request.env.user.id)]) or 0
            pager = portal_pager(
                url="/portal/employee-payslip",
                total=record_len,
                page=page,
                step=self._items_per_page
            )
            payslip_ids = request.env['hr.payslip'].sudo().search(
                domain,
                order=order,
                limit=self._items_per_page,
                offset=pager['offset']
            )
        if not employee:
            return werkzeug.utils.redirect("/portal/home")
        res_dict = {
            'payslip_ids': payslip_ids,
            'employee': employee,
            'has_employee': True,
            'page_name': 'payslips_list_page',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/portal/employee-payslip',
        }
        return request.render('employee_portal_service.employee_payslips_list_page',
                              qcontext=res_dict)

    @http.route('/portal/employee-payslip/<payslip_id>', type='http', auth="user", website=True)
    def details_payslip(self, payslip_id):
        if not payslip_id:
            payslip_id = 0
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        payslip_row = request.env['hr.payslip'].sudo().browse(int(payslip_id))
        return request.render('employee_portal_service.view_payslip_page',
                              qcontext={
                                  'payslip_id': payslip_row,
                                  'employee': employee,
                                  'has_employee': True,
                              })

    @http.route(['/print/payslip-details'], type='http', auth="public", website=True)
    def print_payslip(self, **kwargs):
        pdf, _ = request.env.ref('om_hr_payroll.action_report_payslip').sudo().render_qweb_pdf([int(kwargs.get('id'))])
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf)), ("Content-Disposition", 'filename="reportbk.pdf"')]
        return request.make_response(pdf, headers=pdfhttpheaders)
