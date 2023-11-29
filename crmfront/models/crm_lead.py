from odoo import fields, models, api
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Lead(models.Model):
    _inherit = "crm.lead"
    _rec_name = "lead_number"
    _order = "lead_number desc"
    

#----------LEAD FIELDS-----------------#
    lead_number = fields.Char(string="Lead number", default="/", readonly=True)
    name_reduced = fields.Char(compute="reduce_length")
    @api.depends('name')
    def reduce_length(self):
        for rec in self:
            rec.name_reduced = len((rec.name or '').split(' ')) > 3 and '%s ...' % ' '.join(rec.name.split(' ')[:3]) or rec.name
    
    category_name = fields.Char(
        string='category_name',
    )
    category_id = fields.Many2one(
        comodel_name="crm.lead.category",
        string="Category Name",
    )
    service_id = fields.Many2one(
        comodel_name="product.template",
        string="Service Name",
        domain=[('type', '=', 'service')],
    )
    partner_name = fields.Char(
        'Customer Name', tracking=20, index=True,
        compute='_compute_partner_name', readonly=False, store=True,
        help='The name of the future partner company that will be created while converting the lead into opportunity')
    comments_count = fields.Integer(string='Comments', compute='_compute_comments')
    def _compute_comments(self):
        for record in self:
            comments = self.env['mail.message'].search_count(
                [('res_id', '=', record.id), ('message_type', '=', 'comment'), ('model', '=', 'crm.lead')])
            record.comments_count = comments
    def action_view_comments(self):
        for record in self:
            pass
    
    
#---------MODEL FUNCTIONS----------#
    def _prepare_lead_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_context(self.with_company(values["company_id"]))
        return seq.next_by_code("crm.lead.sequence") or "/"
    
    @api.model_create_multi
    def create(self, vals_list):
        if vals_list[0].get("lead_number", "/") == "/":
            vals_list[0]["lead_number"] = self._prepare_lead_number(vals_list[0])

        for vals in vals_list:
            if vals.get('website'):
                vals['website'] = self.env['res.partner']._clean_website(
                    vals['website'])

        users = self.env.ref('crmfront.business_admin').users.search([
            ('company_id', '=', vals['company_id'])
        ])
        if users:
            user = random.choice(users)
            vals_list[0]['user_id'] = user.id

        leads = super(Lead, self).create(vals_list)
        for lead in leads:
            if lead:
                self.new_customer_lead_email(lead)
            if lead.user_id:
                self.new_assigned_user_ticket_email(lead)
        
        for lead, values in zip(leads, vals_list):
            if any(field in ['active', 'stage_id'] for field in values):
                lead._handle_won_lost(values)

        return leads

    def name_get(self):
        result = []
        for record in self:
            name = record.lead_number
            result.append((record.id, name))
        return result
    
    def _message_get_suggested_recipients(self):
        pass

    def new_assigned_user_ticket_email(self, obj):
        template = self.env.ref('crmfront.assigned_user_lead_email_template')
        if template:
            self.env['mail.template'].browse(
                template.id).send_mail(obj.id, force_send=True)

    def new_customer_lead_email(self, obj):
        template = self.env.ref('crmfront.customer_lead_email_template')
        if template:
            self.env['mail.template'].browse(
                template.id).send_mail(obj.id, force_send=True)    
    

#----BACKEND CRM DASHBOARD FUNCTIONS-------------#   
    @api.model
    def get_lead_count(self, uid):
        labels = ['LEADS']
        
        crm_all_leads = self.env["crm.lead"].search_count([])
        
        crm_leads_count = self.env['crm.lead'].search_count([
            ('company_id', '=', uid['allowed_company_ids'][0]),
            ('type','=','lead')
        ])

        crm_leads_won_count = self.env['crm.lead'].search_count([
            ('company_id', '=', uid['allowed_company_ids'][0]),
            ('stage_id','=',4)
        ])

        crm_opportunities_count = self.env['crm.lead'].search_count([
            ('company_id', '=', uid['allowed_company_ids'][0]),
            ('type','=','opportunity')
        ])

        lead_percentage = round((crm_leads_count /crm_all_leads) * 100, 1)
        opportunity_percentage = round((crm_opportunities_count /crm_all_leads) * 100, 1)
        crm_leads_won_percentage = round((crm_leads_won_count /crm_all_leads) * 100, 1)

        records = {
            'labels':labels,
            'crm_leads_count':crm_leads_count,
            'lead_percentage': lead_percentage,
            'opportunity_percentage':opportunity_percentage,
            'crm_leads_won_count':crm_leads_won_percentage,
        }
        return  records

    @api.model
    def click_leads(self):
        lead_list_id = self.env.ref('crm.crm_case_tree_view_leads').id
        lead_form_id = self.env.ref('crm.crm_lead_view_form').id
        result = {
            'lead_list_id': lead_list_id,
            'lead_form_id': lead_form_id,
            'event':'clicked',
        }
        return result

    @api.model
    def get_opportunity_count(self, uid):
        labels = ['OPPORTUNITIES']
        crm_opportunities_count = self.env['crm.lead'].search_count([
            ('company_id', '=', uid['allowed_company_ids'][0]),
            ('type','=','opportunity')
        ])
        records = {
            'labels':labels,
            'crm_opportunities_count':crm_opportunities_count,
        }
        return records

    @api.model
    def click_opportunities(self):
        result = {
            'event':'clicked',
        }
        return result

    @api.model
    def get_leads_by_month(self, uid):
        leads_dict = []
        leads_labels = []
        current_date = datetime.now()
        x = 1
        leads_labels.append(current_date.strftime("%b - %y"))
        leadsnumber = self.env['crm.lead'].search_count([
                    ('type', '=', 'lead'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', current_date.strftime('%Y-%m-01')),
                    ('create_date', '<', (current_date + relativedelta(months=1)).strftime('%Y-%m-01'))
                ])
        leads_dict.append(leadsnumber)
            
        while x <= 4:
            date2 =  current_date - relativedelta(months=x)
            leads_labels.append(date2.strftime("%b - %y"))
            leadsnumber = self.env['crm.lead'].search_count([
                    ('type', '=', 'lead'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', date2.strftime('%Y-%m-01')),
                    ('create_date', '<', (date2 + relativedelta(months=1)).strftime('%Y-%m-01')),
                ])
            leads_dict.append(leadsnumber)
            x = x+1

        leads_dict.reverse()
        leads_labels.reverse()
        
        records = { 
            'leads_labels':leads_labels,
            'leads_dict':leads_dict,
        }
        return  records

    @api.model
    def get_leads_to_opportunities(self, uid):
        leads_dict = []
        leads_labels = []
        current_date = datetime.now()
        x = 1
        leads_labels.append(current_date.strftime("%b - %y"))
        leadsnumber = self.env['crm.lead'].search_count([
                    ('type','=','opportunity'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', current_date.strftime('%Y-%m-01')),
                    ('create_date', '<', (current_date + relativedelta(months=1)).strftime('%Y-%m-01'))
                ])
        leads_dict.append(leadsnumber)
            
        while x <= 4:
            date2 =  current_date - relativedelta(months=x)
            leads_labels.append(date2.strftime("%b - %y"))
            leadsnumber = self.env['crm.lead'].search_count([
                    ('type','=','opportunity'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', date2.strftime('%Y-%m-01')),
                    ('create_date', '<', (date2 + relativedelta(months=1)).strftime('%Y-%m-01')),
                ])
            leads_dict.append(leadsnumber)
            x = x+1

        leads_dict.reverse()
        leads_labels.reverse()
        
        records = { 
            'leads_labels':leads_labels,
            'leads_dict':leads_dict,
        }
        return  records

    @api.model
    def get_leads_vs_opportunities(self, uid):
        opportunities_dict = []
        leads_dict = []
        opportunities_labels = []
        
        current_date = datetime.now()
        x = 1
        total = 0 
        opportunities_labels.append(current_date.strftime("%b - %y"))
        opportunitiesnumber = self.env['crm.lead'].search_count([
                    ('type', '=', 'opportunity'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', current_date.strftime('%Y-%m-01')),
                    ('create_date', '<', (current_date + relativedelta(months=1)).strftime('%Y-%m-01'))
                ])
        opportunities_dict.append(opportunitiesnumber)
        total = total + opportunitiesnumber
            
        leadsnumber = self.env['crm.lead'].sudo().search_count([
                    ('type', '=', 'lead'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', current_date.strftime('%Y-%m-01')),
                    ('create_date', '<', (current_date + relativedelta(months=1)).strftime('%Y-%m-01'))
                ])
        leads_dict.append(leadsnumber)
        total = total + leadsnumber
        while x <= 12:
            date2 =  current_date - relativedelta(months=x)
            opportunities_labels.append(date2.strftime("%b - %y"))
            opportunitiesnumber = self.env['crm.lead'].search_count([
                    ('type', '=', 'opportunity'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', date2.strftime('%Y-%m-01')),
                    ('create_date', '<', (date2 + relativedelta(months=1)).strftime('%Y-%m-01')),
                ])
            opportunities_dict.append(opportunitiesnumber)
            total = total + opportunitiesnumber
            leadsnumber = self.env['crm.lead'].sudo().search_count([
                    ('type', '=', 'lead'),
                    ('company_id', '=', uid['allowed_company_ids'][0]),
                    ('create_date', '>=', date2.strftime('%Y-%m-01')),
                    ('create_date', '<', (date2 + relativedelta(months=1)).strftime('%Y-%m-01')),
                ])
            leads_dict.append(leadsnumber)
            total = total + leadsnumber
            
            x = x+1
        
        opportunities_dict.reverse()
        leads_dict.reverse()
        opportunities_labels.reverse()
        records = { 
            'opportunities_labels':opportunities_labels,
            'opportunities_dict':opportunities_dict,
            'leads_dict':leads_dict,
            'total':total,
        }
        return  records

    @api.model
    def leads_per_service(self, uid ):
        leads_dict = []
        leads_labels = []

        services = self.env['product.template'].search([
            ('type', '=', 'service')
        ])
        for i in services:
            leads_labels.append(i.name)
            service_count = self.env['crm.lead'].search_count([
                    ('service_id', '=', i.id),
                ])
            leads_dict.append(service_count)
        records = { 
            'leads_labels':leads_labels,
            'leads_dict':leads_dict,
            
        }
        return records

        


        