from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
import werkzeug.urls
import re


class Partner(models.Model):
    _inherit = "res.partner"

#----------PARTNER FIELDS-----------------#
    @api.onchange("phone")
    def onchange_phone(self):
        if self.phone == False:
            self.phone = self.phone
        else:
            self.phone = re.sub('[^0-9+]','', self.phone)

    employee_ids = fields.Many2many(
        string='Employees',
        comodel_name='hr.employee',
        relation='customer_employee_rel',
        column1='partner_id',
        column2='employee_id',
    )
    company_ids = fields.Many2many(
        string="Companies",
        comodel_name = 'res.company',
        relation ='customer_company_rel',
        column1='partner_id',
        column2='company_id',
    )
    contact_type = fields.Selection(
        string='Customer Category',
        selection=[('ORDINARY', 'ORDINARY'), (
            'VIP', 'VIP'), ('PREMIUM', 'PREMIUM')],
        default='ORDINARY'
    )
    inventory_count = fields.Integer(
        string='Inventory', compute="_compute_inventory_count"
    )
    warehouse_id = fields.Many2one(
        string=' Nearest Warehouse',
        comodel_name='stock.warehouse',
        ondelete='restrict',
    )
    active_contracts_count = fields.Integer(
        compute="_compute_active_contracts", string="Contracts"
    )
    customer = fields.Boolean(
        string='customer',
    )

#----------------MODEL FUNCTIONS------------------#
    def _compute_inventory_count(self):
        for record in self:
            record.inventory_count = self.env['stock.picking'].search_count(
                [('picking_type_id.code', '=', 'outgoing'), ('partner_id', '=', record.id)])

    def action_view_inventory(self):
        for record in self:
            return {
                "name": "Delivery Orders",
                "view_type": "form",
                "view_mode": "tree,kanban,form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                "domain": [('picking_type_id.code', '=', 'outgoing'), ('partner_id', '=', record.id)],
            }

    def _get_signup_url_for_action(self, url=None, action=None, view_type=None, menu_id=None, res_id=None, model=None):
        """ generate a signup url for the given partner ids and action, possibly overriding
            the url state components (menu_id, id, view_type) """

        res = dict.fromkeys(self.ids, False)
        for partner in self:
            base_url = partner.get_base_url()
            
            # when required, make sure the partner has a valid signup token
            if self.env.context.get('signup_valid') and not partner.user_ids:
                partner.sudo().signup_prepare()

            route = 'login'
            # the parameters to encode for the query
            query = dict(db=self.env.cr.dbname)
            signup_type = self.env.context.get(
                'signup_force_type_in_url', partner.sudo().signup_type or '')
            if signup_type:
                route = 'reset_password' if signup_type == 'reset' else signup_type

            if partner.sudo().signup_token and signup_type:
                query['token'] = partner.sudo().signup_token
            elif partner.user_ids:
                query['login'] = partner.user_ids[0].login
            else:
                continue        # no signup token, no user, thus no signup url!

            if url:
                query['redirect'] = url
            else:
                fragment = dict()
                base = '/web#'
                if action == '/mail/view':
                    base = '/mail/view?'
                elif action:
                    fragment['action'] = action
                if view_type:
                    fragment['view_type'] = view_type
                if menu_id:
                    fragment['menu_id'] = menu_id
                if model:
                    fragment['model'] = model
                if res_id:
                    fragment['res_id'] = res_id

                if fragment:
                    query['redirect'] = base + \
                        werkzeug.urls.url_encode(fragment)

            url = "/web/%s?%s" % (route, werkzeug.urls.url_encode(query))
            if not self.env.context.get('relative_url'):
                url = werkzeug.urls.url_join(base_url, url)
            res[partner.id] = url
        return res

    @api.model
    def create(self, vals_list):
        
        
        if 'email' in vals_list:
            partner_exists = self.env['res.partner'].search([('email','=',vals_list['email'])],
            limit=1
            )
            if partner_exists:
                raise ValidationError(_("Customer with email address {} already exists".format(partner_exists.email)))

        is_customer = False
        if 'company_type' in vals_list:
            is_customer = True
            vals_list.update({
                'customer':True,
            })       
            
        if 'employee_ids' in vals_list:
            if vals_list['employee_ids'][0][2]:
                for item in vals_list['employee_ids'][0][2]:
                    customers = self.env['res.partner'].search([('customer', '=', True)])
                    for customer in customers:
                        if customer.employee_ids:
                            for id in customer.employee_ids:
                                if id.id == item:
                                    raise ValidationError(_("Employee {} was deployed to customer {} .\nPlease select another employee".format(
                                        id.name, customer.name)))

                    rel_employee = self.env['hr.employee'].search(
                        [('id', '=', item)])
                    rel_employee.write({
                        'address_id': self.id
                    })

        partner = super(Partner, self).create(vals_list)
        
        if is_customer:
            user = self.env['res.users'].search([('login','=',partner.email)],
            limit=1
            )
            if user:
                user.write({
                    'customer':True
                })
        return partner

    def write(self, values):
        # storing the record before editing if the employee_id has any field
        prev_employee_list = []
        if 'employee_ids' in values:
            for record in self:
                if record.employee_ids:
                    for emp in record.employee_ids:
                        prev_employee_list.append(emp.id)

        partner = super(Partner, self).write(values)

        # get current employees added in the list:
        current_employee_list = []
        if 'employee_ids' in values:
            for record in self:
                for emp in record.employee_ids:
                    current_employee_list.append(emp.id)

        if 'employee_ids' in values:
            # on addition of an employee
            for item in current_employee_list:
                if item not in prev_employee_list:
                    customers = record.env['res.partner'].search([('customer', '=', True)])
                    for customer in customers:
                        # checking if not current customer
                        if customer.id != record.id:
                            # check employees of active customer
                            if customer.employee_ids:
                                for employee in customer.employee_ids:
                                    # if this employee is already deployed
                                    if employee.id == item:
                                        raise ValidationError(_("Employee {} was deployed to customer {} .\nPlease select another employee".format(
                                            employee.name, customer.name)))

                    rel_employee = record.env['hr.employee'].search(
                        [('id', '=', item)])
                    rel_employee.write({
                        'address_id': record.id
                    })
            # on removal of an employee
            for id in prev_employee_list:
                if id not in current_employee_list:
                    employee = record.env['hr.employee'].search(
                        [("id", "=", id)])
                    employee.write({
                        'address_id': False
                    })

        return partner

#----------BACKEND CRM DASHBOARD FUNCTIONS---------#       
    @api.model
    def get_customer_count(self, uid ):
        labels = ['CUSTOMERS']
        crm_customers_count = self.env['res.partner'].search_count([
            ('company_ids', '=', uid['allowed_company_ids'][0]),
            ('customer','=',True)
        ])
        records = {
            'labels':labels,
            'crm_customers_count':crm_customers_count,
        }
        return  records

    @api.model
    def click_customers(self):
        result = {
            'event':'clicked',
        }
        return result
