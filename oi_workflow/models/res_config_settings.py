'''
Created on Jun 28, 2020

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    module_oi_workflow_expense = fields.Boolean(string='Employee Expenses')
    module_oi_workflow_hr_contract = fields.Boolean(string='Employee Contracts')
    module_oi_workflow_hr_holidays = fields.Boolean(string='Employee Time Off')
    module_oi_workflow_hr_holidays_manager = fields.Boolean(string='Employee Time Off / Employee Manager')
    module_oi_workflow_hr_payslip_run = fields.Boolean(string='Payslip Batches')
    module_oi_workflow_purchase_order = fields.Boolean(string='Purchase Order')
    module_oi_workflow_purchase_requisition = fields.Boolean(string='Purchase Agreements')
    module_oi_workflow_sale_order = fields.Boolean(string='Sale Order')
        
    @api.onchange('module_oi_workflow_expense','module_oi_workflow_hr_contract','module_oi_workflow_hr_holidays',
                  'module_oi_workflow_hr_holidays_manager','module_oi_workflow_hr_payslip_run','module_oi_workflow_purchase_order',
                  'module_oi_workflow_purchase_requisition','module_oi_workflow_sale_order')
    def _onchange_workflow(self):
        for name in ('module_oi_workflow_expense','module_oi_workflow_hr_contract','module_oi_workflow_hr_holidays',
                  'module_oi_workflow_hr_holidays_manager','module_oi_workflow_hr_payslip_run','module_oi_workflow_purchase_order',
                  'module_oi_workflow_purchase_requisition','module_oi_workflow_sale_order'):            
            module_name = name[7:]
            if self[name]:
                if not self.env["ir.module.module"].get_module_info(module_name):    
                    self[name] = False                
                    return {
                        'warning' : {
                            'title' : 'Module not found',
                            'message' : """Module (%s) is not available in your system
Please download it from                            
https://apps.odoo.com/apps/13.0/%s/""" % (module_name,module_name)
                            }
                        }