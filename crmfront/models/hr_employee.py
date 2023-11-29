from odoo import fields, models, api, _

# class HrEmployeeBase(models.Model):
#     _inherits = 'hr.employee.base'

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    service_id = fields.Many2one(
        comodel_name="product.template",
        string="Service",
        domain=[('type', '=', 'service')],
    )

    employed = fields.Boolean(
        compute='_compute_employed')

    def _compute_employed(self):
        for record in self:
            if not record.address_id:
                record.employed = False
            else:
                record.employed = True

    def write(self, values):
        prev_customer_id = 0
        for record in self:
            if record.address_id:
                prev_customer_id = record.address_id.id

        res = super(HrEmployee, self).write(values)
        for record in self:
            if 'address_id' in values:
                # if the address_id is true
                if values['address_id']:
                   # if the address_id is true but the employee prevously had one
                    if prev_customer_id:
                        customer_had_employee = record.env['res.partner'].search(
                            [('id', '=', prev_customer_id)])
                        customer_had_employee.write({
                            'employee_ids': [(3, record.id)]
                        })
                    # if the employee never had an address field before
                    record.address_id.write({
                        'employee_ids': [(4, record.id)]
                    })
                # if the address_id is false but the employee prevously had one
                else:

                    customer = record.env['res.partner'].search(
                        [('id', '=', prev_customer_id)])
                    for emp in customer.employee_ids:
                        if emp.id == record.id:
                            customer.write({
                                'employee_ids': [(3, record.id)]
                            })
        return res

    @api.model
    def create(self, values):
        employee = super(HrEmployee, self).create(values)
        if 'address_id' in values:
            customer = self.env['res.partner'].search(
                [('id', '=', values['address_id'])])
            customer.write({
                'employee_ids': [(4, employee.id)]
            })

        return employee
