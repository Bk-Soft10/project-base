# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WebNotification(models.Model):
    _name = 'web.notification'
    _description = 'Web Notification'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    notification_type = fields.Selection([
        ('popup', 'Pop-Up type'),
        ('breaking_news', 'Breaking News type'),
    ], string='Notifications Type', required=True, default='popup')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('finish', 'Finish'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', tracking=True)
    
    # General Information
    user_selection = fields.Selection([
        ('among', 'Among'),
        ('all', 'ALL'),
    ], string='Users', default='all', required=True)
    
    user_ids = fields.Many2many(
        'res.users',
        'web_notification_user_rel',
        'notification_id',
        'user_id',
        string='Users'
    )
    
    message = fields.Text(string='Message', required=True)
    template_id = fields.Many2one('web.notification.template', string='Template')

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.message = self.template_id.message
    
    # Breaking News specific fields
    background_color = fields.Char(string='Background color', default='#FFFFFF')
    font_color = fields.Char(string='Font color', default='#000080')
    font_size = fields.Integer(string='Font Size(px)', default=30)
    is_moving_text = fields.Boolean(string='Moving Text?', default=True)
    moving_text_direction = fields.Selection([
        ('rtl', 'Right to Left'),
        ('ltr', 'Left to Right'),
    ], string='Moving Text Dir', default='rtl')
    expiry_date = fields.Datetime(string='Breaking News Popup Expiry Date')
    
    # Read tracking
    read_ids = fields.One2many(
        'web.notification.read',
        'notification_id',
        string='Read By Users'
    )
    
    def action_submit(self):
        """Submit notification - change state to in_progress"""
        for record in self:
            if record.state == 'draft':
                record.state = 'in_progress'
            elif record.state == 'in_progress':
                record.state = 'finish'
        return True
    
    def action_set_draft(self):
        """Set state to draft"""
        self.write({'state': 'draft'})
        return True
    
    def action_set_in_progress(self):
        """Set state to in progress"""
        self.write({'state': 'in_progress'})
        return True
    
    def action_set_finish(self):
        """Set state to finish"""
        for rec in self:
            rec.state = 'finish'
            if rec.message:
                rec.message = f"{rec.message} [Finished]"
            else:
                rec.message = "[Finished]"
        return True
    
    def action_cancel(self):
        """Set state to cancelled"""
        for rec in self:
            rec.state = 'cancelled'
            if rec.message:
                rec.message = f"{rec.message} [Cancelled]"
            else:
                rec.message = "[Cancelled]"

    @api.model
    def get_active_notifications(self):
        """Get active notifications for current user"""
        current_user = self.env.user
        
        # Get notifications that user has already read
        read_notification_ids = self.env['web.notification.read'].sudo().search([
            ('user_id', '=', current_user.id)
        ]).mapped('notification_id').ids
        
        domain = [
            ('state', '=', 'in_progress'),
            ('id', 'not in', read_notification_ids),
            '|',
            ('user_selection', '=', 'all'),
            ('user_ids', 'in', [current_user.id])
        ]
        
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("Fetching notifications for user %s (ID: %s)", current_user.name, current_user.id)
        _logger.info("Read notification IDs: %s", read_notification_ids)
        _logger.info("Search domain: %s", domain)
        
        notifications = self.search(domain)
        _logger.info("Found %s notifications", len(notifications))
        
        result = {
            'popup': [],
            'breaking_news': []
        }
        
        for notif in notifications:
            # Check expiry for breaking news
            if notif.notification_type == 'breaking_news' and notif.expiry_date:
                if fields.Datetime.now() > notif.expiry_date:
                    continue
            
            notif_data = {
                'id': notif.id,
                'name': notif.name,
                'message': notif.message,
                'type': notif.notification_type,
            }
            
            if notif.notification_type == 'popup':
                result['popup'].append(notif_data)
            else:
                notif_data.update({
                    'background_color': notif.background_color or '#FFFFFF',
                    'font_color': notif.font_color or '#000080',
                    'font_size': notif.font_size or 30,
                    'is_moving_text': notif.is_moving_text,
                    'moving_text_direction': notif.moving_text_direction or 'rtl',
                })
                result['breaking_news'].append(notif_data)
        
        return result
    
    @api.model
    def get_notification_history(self):
        """Get read notifications for current user"""
        current_user = self.env.user
        
        # Get notifications that user has already read
        read_notification_ids = self.env['web.notification.read'].sudo().search([
            ('user_id', '=', current_user.id)
        ]).mapped('notification_id').ids
        
        domain = [
            '|',
            ('id', 'in', read_notification_ids),
            '|',
            ('state', '=', 'finish'),
            ('state', '=', 'cancelled'),
            '|',
            ('user_selection', '=', 'all'),
            ('user_ids', 'in', [current_user.id])
        ]
        
        notifications = self.search(domain, limit=20, order='create_date desc')
        
        result = []
        for notif in notifications:
            result.append({
                'id': notif.id,
                'name': notif.name,
                'message': notif.message,
                'type': notif.notification_type,
                'date': notif.create_date,
                'state': notif.state,
            })
        
        return result
    
    @api.model
    def mark_as_read(self, notification_id):
        """Mark notification as read for current user"""
        current_user = self.env.user
        existing = self.env['web.notification.read'].sudo().search([
            ('notification_id', '=', notification_id),
            ('user_id', '=', current_user.id)
        ], limit=1)
        
        if not existing:
            self.env['web.notification.read'].sudo().create({
                'notification_id': notification_id,
                'user_id': current_user.id,
            })
        return True

    def action_delete_notification(self):
        self.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
