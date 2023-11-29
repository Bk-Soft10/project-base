from odoo import fields, models, api, _


class LeadCategory(models.Model):
    _name = "crm.lead.category"
    _description = "Lead Category"
    
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    
    name = fields.Char(
        string="Name",
        required=True,
    )
     
    lead_ids = fields.One2many(
        comodel_name="crm.lead",
        inverse_name="category_id",
        string="Leads",
    )
    
    pending_lead_count = fields.Integer(
        string="Number Of Pending Leads", compute="_compute_pending_leads",
    )

    in_progress_lead_count = fields.Integer(
        string="Number of In Progress Leads", compute="_compute_in_progress_leads",
    )
    done_lead_count = fields.Integer(
        string="Number of Done Leads", compute="_compute_done_leads",
    )
    cancelled_lead_count = fields.Integer(
        string="Number of Cancelled Leads", compute="_compute_cancelled_leads",
    )

    @api.depends_context('category_id')
    @api.depends("lead_ids", )
    def _compute_pending_leads(self):
        for record in self:
            count = 0
            for lead in record.lead_ids:
                if lead.category_id.id == record.id and lead.stage_id.id == 1 or\
                        lead.stage_id.id == 2 or lead.stage_id.id == 3:
                    count += 1
            record.pending_lead_count = count

    @api.depends("lead_ids", )
    def _compute_in_progress_leads(self):
        for record in self:
            count = 0
            for lead in record.lead_ids:
                if lead.category_id.id == record.id and lead.stage_id.id == 1 or\
                        lead.stage_id.id == 2 or lead.stage_id.id == 3:
                    count += 1
            record.in_progress_lead_count = count

    @api.depends("lead_ids", )
    def _compute_done_leads(self):
        for record in self:
            count = 0
            for lead in record.lead_ids:
                if lead.category_id.id == record.id and lead.stage_id.id == 4:
                    count += 1
            record.done_lead_count = count

    @api.depends("lead_ids", )
    def _compute_cancelled_leads(self):
        for record in self:
            count = 0
            for lead in record.lead_ids:
                if lead.category_id.id == record.id and lead.stage_id.id == 5:
                    count += 1
            record.cancelled_lead_count = count

    def open_pending_leads(self):
        for record in self:
            return{
                'name': _('Leads'),
                'domain': [('category_id', '=', record.id), ('stage_id', '=', [1, 2, 3])],
                'view_type': 'form',
                'res_model': 'crm.lead',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }
            
    def open_in_progress_leads(self):
        for record in self:
            return{
                'name': _('Leads'),
                'domain': [('category_id', '=', record.id), ('stage_id', '=', [1, 2, 3])],
                'view_type': 'form',
                'res_model': 'crm.lead',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }
            
    def open_done_leads(self):
        for record in self:
            return{
                'name': _('Leads'),
                'domain': [('category_id', '=', 1), ('stage_id', '=', 4)],
                'view_type': 'form',
                'res_model': 'crm.lead',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }
            
    def open_cancelled_leads(self):
        for record in self:
            return{
                'name': _('Leads'),
                'domain': [('category_id', '=', 1), ('stage_id', '=', 0)],
                'view_type': 'form',
                'res_model': 'crm.lead',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }
            