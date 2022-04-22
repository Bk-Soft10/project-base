'''
Created on Nov 12, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval

class AppraisalBatch(models.Model):    
    _name = 'appraisal.batch'
    _description = 'Appraisal Batch'
    _order = 'start_date desc'
    
    name = fields.Char(required = True)
    active = fields.Boolean(default = True)    
    start_date = fields.Date('Start Date', required = True)
    end_date = fields.Date('End Date', required = True)    
    year = fields.Char(compute ='_calc_year', store = True)
    
    appraisal_ids = fields.One2many('appraisal', 'batch_id')
    appraisal_count = fields.Integer(compute = '_calc_appraisal_count')
    appraisal_draft_count = fields.Integer(compute = '_calc_appraisal_count')
    
    type_id = fields.Many2one('appraisal.batch.type', required = True)
    
    _sql_constraints= [
            ('name_unqiue', 'unique(name)', 'Name must be unique!')
        ]        
    
    @api.onchange('name')
    def _onchange_name(self):
        if self.name and self.name.isdigit() and len(self.name)==4 and self.name[0]=='2':
            self.start_date = '%s-01-01' % self.name
            self.end_date = '%s-12-31' % self.name
    
    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_('Start Date > End Date'))
    
    @api.depends('end_date')
    def _calc_year(self):
        for record in self:
            record.year = record.end_date and record.end_date.year
    
    @api.depends('appraisal_ids')
    def _calc_appraisal_count(self):
        for record in self:
            domain = [('batch_id', '=', record.id)]
            record.appraisal_count = self.env['appraisal'].search(domain, count = True)
            domain.append(('state','=', 'draft'))
            record.appraisal_draft_count = self.env['appraisal'].search(domain, count = True)
                        
    
    def action_view_appraisal(self):
        action, = self.env.ref('oi_appraisal.act_appraisal').read()
        action['domain'] = [('batch_id', 'in', self.ids)]
        return action
    
    
    def action_submit_appraisal(self):
        count = 0
        for appraisal in self.appraisal_ids:
            if appraisal.state=='draft':
                appraisal.action_approve()
                count +=1
        self.env.user.notify_info(_('%s Appraisal(s) Submitted') % count)                        
    
    
    def _generate(self, employee):
        if self.env['appraisal'].search([('batch_id','=', self.id), ('employee_id','=', employee.id)], limit = 1):
            return self.env['appraisal']
        
        template_id = False
        
        for template in self.env['appraisal.template'].search([]):
            if template.domain:
                domain = safe_eval(template.domain)        
                if not employee.filtered_domain(domain):
                    continue
                
            if template.job_ids and employee.job_id not in template.job_ids:
                continue
            
            template_id = template
            break
                    
        if not template_id:
            raise UserError(_('No Appraisal Template assign for %s') % employee.name)
        
        appraisal = self.env['appraisal'].create({
            'batch_id' : self.id,
            'employee_id' : employee.id,
            'template_id' : template_id.id,
            })
        sequence = 0
        for section in template_id.sections_ids:
            for question in section.question_ids:
                if question.job_ids and employee.job_id not in question.job_ids:
                    continue                
                sequence +=1
                vals, = question.read(['section_id', 'name', 'description', 'weight'], load = False)
                vals.pop('id')
                vals.update({
                    'appraisal_id' : appraisal.id,
                    'sequence' : sequence,
                    'question_id' : question.id
                    })
                self.env['appraisal.line'].create(vals)
        return appraisal