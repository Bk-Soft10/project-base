from odoo import fields, api, models, _

class Product(models.Model):
    _inherit = ["product.template"]

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=1,
    )

    @api.model
    def get_service_count(self, uid):
        labels = ['SERVICES']
        service_count = self.env['product.template'].search_count([
            ('company_id', '=', uid['allowed_company_ids'][0]),
            ('type','=','service')
        ])
        records = {
            'labels':labels,
            'services_count':service_count,
        }
        return  records

    @api.model
    def click_services(self):
        service_kanban_id = self.env.ref('product.product_template_kanban_view').id
        service_form_id = self.env.ref('product.product_template_only_form_view').id
        result = {
            'service_kanban_id': service_kanban_id,
            'service_form_id': service_form_id,
            'event':'clicked',
        }
        return result
