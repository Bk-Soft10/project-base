'''
Created on Jul 8, 2019

@author: Zuhair Hammadi
'''
from odoo import models, api

class Users(models.Model):
    _inherit = 'res.users'

    @api.model
    def systray_get_activities(self):
        res = super(Users, self).systray_get_activities()
        for activity_data in res:
            if activity_data.get('type')=='activity':
                action_ids = self.env['ir.actions.act_window'].search([('res_model','=', activity_data['model'])])
                menu_ids = self.env['ir.ui.menu']
                for action_id in action_ids:
                    menu_ids += self.env['ir.ui.menu'].search([('action','=', 'ir.actions.act_window,%d' % action_id.id)])
                menu_id = menu_ids.sorted()[:1]
                main_menu_id = menu_id
                while main_menu_id.parent_id:
                    main_menu_id = main_menu_id.parent_id
                activity_data['main_menu_id'] = main_menu_id.id
                                
                if menu_id.web_icon_data:
                    activity_data["icon"] = "/web/image/%s/%d/web_icon_data" % (menu_id._name, menu_id.id)
                elif main_menu_id.web_icon_data:
                    activity_data["icon"] = "/web/image/%s/%d/web_icon_data" % (main_menu_id._name, main_menu_id.id)
                                
        return res
