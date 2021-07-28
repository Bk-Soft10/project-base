'''
Created on Nov 14, 2019

@author: Zuhair Hammadi
'''
from odoo import api, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {'lang' : None})
        menu_ids = env['ir.ui.menu'].search([('parent_id', '=', env.ref('oi_workflow.menu_approval_config').id)])        
        if menu_ids:
            _logger.info('Delete menu_ids' % menu_ids)
            action_ids = menu_ids.mapped('action')
            menu_ids.unlink()
            action_ids.unlink()