from markupsafe import Markup

from odoo import http, Command
from odoo.http import request
from odoo.addons.mail.tools.discuss import Store

class MessengerSessionController(http.Controller):

    @http.route('/us_messenger/session/data', type='jsonrpc', auth='user')
    def messenger_session_data(self, channel_id):
        """Get messenger session data for a channel."""
        channel = request.env['discuss.channel'].browse(channel_id)
        if not channel.exists():
            return {}
        
        return {
            'messenger_note': channel.messenger_note or '',
            'messenger_status': channel.messenger_status or 'in_progress',
        }

    @http.route('/us_messenger/session/update_note', type='jsonrpc', auth='user')
    def messenger_session_update_note(self, channel_id, note):
        """Update messenger note for a channel."""
        channel = request.env['discuss.channel'].sudo().search([('id', '=', channel_id)])
        if not channel:
            return False
        # sudo: discuss.channel - internal users having the rights to read the session can update its note
        # Markup: note sanitized when written on the field
        channel.sudo().messenger_note = Markup(note)
        return True

    @http.route('/us_messenger/session/update_status', type='jsonrpc', auth='user')
    def messenger_session_update_status(self, channel_id, status):
        """Update messenger status for a channel."""
        channel = request.env['discuss.channel'].search([('id', '=', channel_id)])
        if not channel:
            return False
        # sudo: discuss.channel - internal users having the rights to read the session can update its status
        channel = channel.sudo()

        if status == 'end_session':
            return False

        channel.messenger_status = status
        return True

    @http.route('/us_messenger/session/end_session', type='jsonrpc', auth='user')
    def messenger_session_end_session(self, channel_id):
        channel = request.env['discuss.channel'].sudo().search([('id', '=', channel_id)])
        if not channel:
            return False
        sudo_channel = channel.sudo()
        if sudo_channel.messenger_status != 'end_session':
            bot = sudo_channel.us_messenger_project_id
            if not bot:
                return False
            bot._end_session(sudo_channel, 'end_session')

        return True

    @http.route("/us_messenger/operator/become", type="jsonrpc", auth="user")
    def messenger_become_operator(self, channel_id):
        discuss_channel = request.env["discuss.channel"].sudo().search([("id", "=", channel_id)], limit=1)
        if not discuss_channel:
            return False

        current_user_partner_id = request.env.user.partner_id.id
        if discuss_channel.messenger_operator_id.id == current_user_partner_id:
            return True

        client_partner_id = discuss_channel.messenger_client_partner_id.id
        allowed_partner_ids = [client_partner_id, current_user_partner_id]
        discuss_channel.write({
            'messenger_operator_id': current_user_partner_id,
            'messenger_status': 'in_progress',
        })

        partners_to_remove = discuss_channel.channel_partner_ids.filtered(lambda p: p.id not in allowed_partner_ids)
        store = Store(bus_channel=discuss_channel)
        for partner in partners_to_remove:
            discuss_channel._action_unfollow(partner=partner, post_leave_message=False)
        discuss_channel.add_members(allowed_partner_ids, post_joined_message=False)
        store.add(discuss_channel)
        store.bus_send()
        return True
