# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class WebNotificationController(http.Controller):

    @http.route('/web/notifications/get', type='json', auth='user')
    def get_notifications(self):
        """API endpoint to fetch active notifications for current user"""
        notifications = request.env['web.notification'].sudo().get_active_notifications()
        return notifications
    
    @http.route('/web/notifications/history', type='json', auth='user')
    def get_notification_history(self):
        """API endpoint to fetch notification history"""
        history = request.env['web.notification'].sudo().get_notification_history()
        return history
    
    @http.route('/web/notifications/mark_read', type='json', auth='user')
    def mark_notification_read(self, notification_id):
        """API endpoint to mark a notification as read (won't show again)"""
        result = request.env['web.notification'].sudo().mark_as_read(notification_id)
        return {'success': result}
    
    @http.route('/web/notifications/dismiss', type='json', auth='user')
    def dismiss_notification(self, notification_id):
        """API endpoint to temporarily dismiss a notification (for current session)"""
        return {'success': True}
