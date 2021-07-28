'''
Created on Aug 29, 2018

@author: Zuhair Hammadi
'''
from odoo import http
from odoo.http import request

class UserAudit(http.Controller):
    
    @http.route('/oi_workflow/approval_info', type='json', auth='user')
    def record_info(self, model, record_id):
        data = {
            'lines' : [],
            }
        format_datetime = lambda value : request.env['ir.qweb.field.datetime'].value_to_html(value, {})
        
        record = request.env[model].browse(record_id)
        record.check_access_rights('read')
        record.check_access_rule('read')
        
        record = record.sudo()
        
        if record._isinstance('approval.record'):        
            data['name'] = record.display_name                
            approval_user2_ids = record.mapped('approval_user2_ids')
            if 'committee' in record.state_id and record.state_id.committee:
                def is_approved(user):
                    for log_id in record.log_ids:
                        if log_id.state != record.state:
                            break
                        if log_id.user_id == user:
                            return True
                    return False
                for user in list(approval_user2_ids):
                    if is_approved(user):
                        approval_user2_ids -=user
                
            data['approval_users'] = []
            for user in approval_user2_ids:
                data['approval_users'].append((user.id, user.employee_ids[:1].display_name or user.display_name))
            data['waiting_approval'] = record.waiting_approval
            
            for log in record.log_ids:
                data['lines'].append({
                    'user' : log.user_id.employee_ids[:1].display_name or log.user_id.display_name,
                    'date' : format_datetime(log.date),
                    'old' : log.old_name or '',
                    'new' : log.name,
                    'description' : log.description or ''
                    })
        
        return data
    
    @http.route('/oi_workflow/approval_models', type='json', auth='user')
    def approval_models(self):
        return {
            'approval_models' : request.env['approval.record']._get_approval_models(),
            'disable_edit_on_non_approval' : request.env['ir.config_parameter'].sudo().get_param("disable_edit_on_non_approval") == "True"
            }
    
    @http.route('/oi_workflow/state_models', type='json', auth='user')
    def state_models(self):
        return request.env['ir.model.fields'].search([('name','=', 'state'),('ttype','=', 'selection'), ('store','=', True)]).mapped('model')