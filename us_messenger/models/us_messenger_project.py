import base64
import logging
import uuid
from werkzeug import urls
from odoo.tools.misc import file_open
from odoo import api, fields, models
from odoo.addons.mail.tools.discuss import Store
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
from odoo.http import request
from markupsafe import Markup

from .ir_logging import LOG_ERROR
import traceback

_logger = logging.getLogger(__name__)
DEFAULT_LOG_NAME = "Log"


def edit_text_message(text='', author_name='', is_signature=True):
    '''Delete link on message'''
    splited_text = text.split('<b><a href="')
    # Check last splited parts, if have link on message
    if 'Link on Message' in splited_text[len(splited_text) - 1]:
        # If yes, then delete them
        text = ''.join(splited_text[0:len(splited_text) - 1])
    return "%s\n\n<br/><i>%s</i>" % (text, author_name) if is_signature else text


def check_message(text):
    splited_text = text.split('<div class="o_mail_notification">')[0]
    return len(splited_text) == len(text)


class UsMessengerProject(models.Model):
    _name = "us.messenger.project"
    _description = "Messenger Project"

    '''
    In order to add your own messenger, follow these steps:

    1. Create your model MyMessenger that _inherit 'us.messenger.project'
    2. Extend the selection of the field "bot_type" with a pair
       ('<my_messenger>', 'My messenger')
    3. Add your methods:
       _<my_messenger>_set_webhook
       _<my_messenger>_unset_webhook
       _<my_messenger>_process_message
       _<my_messenger>_send_to_messenger
    '''

    @api.model
    def default_get(self, fields):
        vals = super(UsMessengerProject, self).default_get(fields)
        vals["website_path"] = uuid.uuid4()
        return vals

    @api.model
    def _lang_get(self):
        return self.env['res.lang'].get_installed()

    def _default_operator_ids(self):
        return [(0, 0, {'user_id': self.env.user.id, 'nickname':self.env.user.name})]

    name = fields.Char(
        "Name", 
        help="Your bot name", 
        required=True, 
        default='Enter_bot_name', 
        copy=False,
    )
    active = fields.Boolean(default=True)
    job_ids = fields.One2many("us.messenger.job", "project_id")
    current_job_id = fields.Many2one("us.messenger.job")
    job_count = fields.Integer(compute="_compute_job_count")
    log_ids = fields.One2many("ir.logging", "project_id")
    log_count = fields.Integer(compute="_compute_log_count")
    user_ids = fields.One2many('us.messenger.partner', 'bot_id')
    users_count = fields.Integer(compute="_compute_users_count")
    company_id = fields.Many2one(
        comodel_name="res.company", 
        string="Company", 
        required=True,
        default=lambda self: self.env.company.id,
    )
    token = fields.Char(
        'Token', 
        required=True, 
        default='Token', 
        copy=False,
    )
    bot_type = fields.Selection(
        selection=[],
        string='Bot Type',
        required=True,
    )
    messenger_image = fields.Image(string="Messenger Image")
    state = fields.Selection(
        string='State',
        selection=[
                ("new", "New"), 
                ("active_webhook", "Active Webhook"),
                ("enabled_webhook", "Enabled Webhook")
            ],
        default="new",
        copy=False,
        help="Type is used to separate New, Active Webhook, Not active Webhook",
    )
    operator_ids = fields.One2many(
        'us.messenger.operator', 'bot_id', string='Operators',
        default=_default_operator_ids)

    assistant_id = fields.Many2one(
        'res.partner', 
        string='Assistant', 
        domain=[('is_assistant', '=', True)],
        help="You can integrate ChatGPT Assistant by installing the 'us_assistant' module",
    )
    is_us_assistant_installed = fields.Boolean(compute='_compute_is_us_assistant_installed')
    link_on_bot = fields.Char('Link on Bot', copy=False)
    is_hide_change_operator_user = fields.Boolean(
        'Hide button "Change Operator" for operators',
        help="Hide 'Change Operator' for operators in menu 'Operators'. "
            "If active, operators and admins can change operator for channel. "
            "If no active, only admins",
    )
    channel_template = fields.Char('Channel template', 
            help='Use %(name)s - name partner \n %(botname)s - bot name', 
            default='%(name)s [%(botname)s]'
    )
    is_add_operator_signature = fields.Boolean('Add operator signature', default=True)
    is_forward_explicit_reply_to_document = fields.Boolean(
        'Forward explicit replies to document',
        default=True,
        help="If enabled, when a messenger user explicitly replies to a message that was sent from a document chatter, "
             "the reply will be duplicated to that document's chatter.",
    )
    is_forward_auto_to_document = fields.Boolean(
        'Auto-forward to last document',
        default=False,
        help="If enabled, when a messenger user sends a message (without explicit reply) and the last message "
             "in the channel was from a document chatter, the message will be duplicated to that document's chatter.",
    )
    operator_user_ids = fields.Many2many('res.users', compute='_compute_operator_user_ids', string='Operator Users')
    # webhook fields
    website_path = fields.Char("Website Path")
    webhook_type = fields.Selection(
        [("http", "application/x-www-form-urlencoded"), ("json", "application/json")],
        string="Webhook Type",
        default="json",
    )
    script_id = fields.Many2one(
        comodel_name="us.messenger.script",
        string="Messenger Script",
        help="Script for bot interaction with messenger users. Defines steps such as " \
        "receiving arbitrary questions about the user's phone number or email, connecting to the operator, etc. " \
        "If the field is empty, the user will be added directly to the communication channel without any intermediate steps.",
    )
    are_you_inside = fields.Boolean(
        string='Are you inside the matrix?',
        compute='_are_you_inside', 
        store=False, 
        readonly=True,
    )
    default_lang = fields.Selection(string="Default language", selection=_lang_get)
    
    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends("job_ids")
    def _compute_job_count(self):
        for r in self:
            r.job_count = len(r.job_ids)

    @api.depends("log_ids")
    def _compute_log_count(self):
        for r in self:
            r.log_count = len(r.log_ids)

    @api.depends('user_ids')
    def _compute_users_count(self):
        for r in self:
            r.users_count = len(r.user_ids)

    @api.depends('operator_ids.user_id')
    def _compute_operator_user_ids(self):
        for rec in self:
            rec.operator_user_ids = rec.operator_ids.mapped('user_id')

    @api.depends('assistant_id')
    def _compute_is_us_assistant_installed(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'us_assistant'), ('state', '=', 'installed')
            ],limit=1
        )
        self.is_us_assistant_installed = bool(module.exists())

    def _are_you_inside(self):
        for rec in self:
            rec.are_you_inside = self.env.user.id in rec.operator_ids.mapped('user_id').ids

    # -------------------------------------------------------------------------
    # CONSTRAINT METHODS
    # -------------------------------------------------------------------------

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if len(record.name.split(' ')) != 1:
                raise UserError('Field name must be without spaces')
            
    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.onchange('bot_type')
    def _onchange_messenger_image(self):
        image_path = self._get_messenger_image_path()
        if image_path and not self.messenger_image:
            with file_open(image_path, 'rb') as f:
                self.messenger_image = base64.b64encode(f.read())
    
    # -------------------------------------------------------------------------
    # LOW-LEVEL METHODS
    # -------------------------------------------------------------------------

    def copy_data(self, default=None):
        res = super(UsMessengerProject, self).copy_data(default=default)
        for r in res:
            r['website_path'] = uuid.uuid4()
        return res

    def write(self, vals):
        if 'operator_ids' in vals:
            operators_to_remove_ids = set()  # IDs of us.messenger.operator records
            operators_to_add_ids = set()  # IDs of us.messenger.operator records (for command 4)
            user_ids_to_add = set()  # IDs of res.users (for command 0 - create)
            
            auto_operator_selection = bool(self.env['ir.config_parameter'].sudo().get_param(
                'us_messenger.auto_operator_selection', False))
            add_new_operators_to_channel = bool(self.env['ir.config_parameter'].sudo().get_param(
                'us_messenger.add_new_operators_to_channel', False))

            for command in vals['operator_ids']:
                if command[0] in (2, 3):  # 2 = delete, 3 = unlink
                    operators_to_remove_ids.add(command[1])
                elif command[0] == 0:  # 0 = create new record, vals contains user_id
                    user_id = command[2].get('user_id') if len(command) > 2 else None
                    if user_id:
                        user_ids_to_add.add(user_id)
                elif command[0] == 4:  # 4 = link existing us.messenger.operator record
                    operators_to_add_ids.add(command[1])

            if operators_to_remove_ids:
                operators_to_remove = self.env['us.messenger.operator'].browse(list(operators_to_remove_ids))
                operator_with_channels = next(
                    (op for op in operators_to_remove if op.channel_count > 0), None
                )
                if operator_with_channels:
                    raise ValidationError(_(
                        "Cannot remove operator '%(operator)s' because they have %(count)s unclosed channel(s). "
                        "Please reassign these channels to another operator first.",
                        operator=operator_with_channels.name,
                        count=operator_with_channels.channel_count,
                    ))
                
                partners_to_remove = operators_to_remove.mapped('partner_id')
                bot_channels = self.env['discuss.channel'].search([
                    ('channel_type', 'like', 'us_messenger_%'),
                    ('us_messenger_project_id', '=', self.id),
                ])
                for channel in bot_channels:
                    for partner in partners_to_remove:
                        channel._action_unfollow(partner=partner, post_leave_message=False)

            if add_new_operators_to_channel and not auto_operator_selection:
                partners_to_add = self.env['res.partner']
                if operators_to_add_ids:
                    partners_to_add |= self.env['us.messenger.operator'].browse(list(operators_to_add_ids)).mapped('partner_id')
                if user_ids_to_add:
                    partners_to_add |= self.env['res.users'].browse(list(user_ids_to_add)).mapped('partner_id')
                
                if partners_to_add:
                    bot_channels = self.env['discuss.channel'].search([
                        ('channel_type', 'like', 'us_messenger_%'),
                        ('us_messenger_project_id', '=', self.id),
                        ('messenger_operator_id', '!=', False),
                    ])
                    for channel in bot_channels:
                        channel.add_members(partners_to_add.ids, post_joined_message=False)

        return super(UsMessengerProject, self).write(vals)
    
    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def action_set_webhook(self):
        self.ensure_one()

        action = self.call_messenger_function('_set_webhook')
        
        self.env.cr.commit()
        if action.get("status") == 'success':
            self.write({'state': 'active_webhook'})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Webhook has been set successfully.'),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        self.write({'state': 'enabled_webhook'})
        raise UserError(_('Error by activation webhook: %s') % (action.get('message'),))

    def action_remove_webhook(self):
        self.ensure_one()

        action = self.call_messenger_function('_unset_webhook')

        self.env.cr.commit()
        if action.get("status") == 'success':
            self.state = 'enabled_webhook'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Webhook has been unset successfully.'),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

        self.state = 'active_webhook'
        raise UserError(_('Error by activation webhook: %s') % (action.get('message'),))

    def action_open_instruction(self):
        id_module = self.env['ir.module.module'].search([('name', '=', 'us_' + self.bot_type.lower())]).id
        return {
            'view_mode': 'form',
            'res_model': 'ir.module.module',
            'type': 'ir.actions.act_window',
            'res_id': id_module
        }

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _pre_process_message(self, data):
        return data

    def _process_message(self, data):
        """Process incoming webhook message using messenger-specific parser.

        :param data: Request data.
        :return: Dict with status and message processing notification.
        """
        self.ensure_one()
        
        job = self.env['us.messenger.job'].create_trigger_job(
            self.id, 
            'Process received message'
        )
        job.log('Received raw data: %s' % (data,))

        data = self._pre_process_message(data)
        
        try:
            # Parse message using messenger-specific implementation
            user_ref, username = self.call_messenger_function('_get_user_data', data)
            messenger_partner, is_partner_created = self.create_or_get_partner(user_ref, username, data, job)
            partner = messenger_partner.partner_id
            channel = messenger_partner.channel_id
            if not channel:
                channel = self.create_channel(messenger_partner, data, job)
                messenger_partner.write({'channel_id':channel.id})
            
            # Sent to Odoo channel
            recived_data = self.call_messenger_function('_get_message_data', data)
            if recived_data:
                self.send_to_channel(
                    channel=channel, partner=partner, 
                    body=recived_data.get('body'), 
                    external_id=recived_data.get('external_messenger_id'), 
                    job=job,
                    attachments=recived_data.get('attachments'),
                    parent_msg_id=recived_data.get('parent_msg_id')
                )
            
            if self.script_id:
                steps_msg_kwargs = self._process_actions(messenger_partner, recived_data, is_partner_created)
                self._send_steps(user_ref, steps_msg_kwargs)

            elif not channel.messenger_operator_id:
                channel._messenger_forward_to_operator()

            job.finish_job('done')
            return {'status': 'success', 'parsed_data': 'test'}

        except Exception as e:
            job.log('Error processing message: %s' % (str(e),), level=LOG_ERROR, traceback=traceback.format_exc())
            job.finish_job('failed')
            return {'status': 'error', 'message': str(e)}
        
    def _end_session(self, channel, channel_status):
        messenger_partner = channel.messenger_partner_id

        partners_to_remove = channel.channel_partner_ids.filtered(
            lambda p: p.id != channel.messenger_client_partner_id.id
        )
        for partner in partners_to_remove:
            channel._action_unfollow(partner=partner, post_leave_message=False)
        channel.write({
            'messenger_status': channel_status,
            'messenger_operator_id': None,
        })

        if messenger_partner.current_step_id and self.script_id:
            step_to_process = messenger_partner.current_step_id._fetch_next_step(messenger_partner)
            messenger_partner.current_step_id = None
            msg_step_kwargs = self.script_id._get_steps_kwargs(messenger_partner, dict(body=step_to_process.message), step_to_process)
            self._send_steps(messenger_partner.external_id, msg_step_kwargs)

    def _send_steps(self, user_ref, steps_msg_kwargs):
        for step_msg_data in steps_msg_kwargs:
            channel_message = step_msg_data.get('channel_msg')

            if messenger_msg_kwargs := step_msg_data.get('messenger_msg'):
                result = self._send_to_messenger(user_ref, **messenger_msg_kwargs)
                
                if channel_message and result.get('external_message_id'):
                    channel_message.write({'external_messenger_id': result.get('external_message_id')})

    def send_to_channel(self, channel, partner, body, external_id, job, attachments=None, parent_msg_id=None):
        """Sending a message to the specified channel."""

        parent_id = None
        document_message_id = None
        
        if parent_msg_id:
            # Search for parent message by external_messenger_id
            parent_msg = self.env['mail.message'].search([
                ('res_id', '=', channel.id), 
                ('model', '=', 'discuss.channel'),
                ('external_messenger_id', '=', str(parent_msg_id))
            ], limit=1)
            parent_id = parent_msg.id if parent_msg else None
            
            # Option 1: Explicit reply to a message from document
            if self.is_forward_explicit_reply_to_document and parent_msg and parent_msg.document_message_id:
                document_message_id = parent_msg.document_message_id
        
        # Option 2: Auto-forward if last message in channel was from document (no explicit reply)
        if not document_message_id and not parent_msg_id and self.is_forward_auto_to_document:
            last_doc_msg = self.env['mail.message'].search([
                ('res_id', '=', channel.id),
                ('model', '=', 'discuss.channel'),
            ], order='id desc', limit=1)
            if last_doc_msg:
                document_message_id = last_doc_msg.document_message_id

        # If we have a document to forward to, duplicate message there
        channel_body = body
        if document_message_id:
            try:
                document = self.env[document_message_id.model].browse(document_message_id.res_id)
                if document.exists():
                    doc_message = document.with_context(mail_create_nosubscribe=True).message_post(
                        body=Markup(body),
                        author_id=partner.id,
                        message_type='comment',
                        subtype_xmlid="mail.mt_note",
                        attachments=attachments,
                    )
                    # Add link to document message in channel body
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    message_link = '%s/mail/message/%s' % (base_url, doc_message.id)
                    doc_name = document.display_name or document.name if hasattr(document, 'name') else ''
                    link_text = 'Link on Message "%s"' % doc_name if doc_name else 'Link on Message'
                    channel_body = '%s<br/><br/><b><a href="%s">%s</a></b>' % (body, message_link, link_text)
                    document_message_id = doc_message.id
                else:
                    document_message_id = None
            except Exception as e:
                job.log('Failed to forward message to document: %s' % str(e), level=LOG_ERROR)
                document_message_id = None

        channel_message = channel.sudo().message_post(
            body=Markup(channel_body),
            author_id=partner.id,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            attachments=attachments,
            parent_id=parent_id,
            external_messenger_id=external_id,
            document_message_id=document_message_id,
        )
        
        return channel_message

    def create_or_get_partner(self, user_ref, username, data, job):
        ''' Creating or obtaining a partner based on data.'''

        messenger_partner = self.user_ids.search([('external_id','=',user_ref), ('bot_id', '=', self.id)])
        is_new_partner = not bool(messenger_partner)
        if is_new_partner:
            params = self.env['res.partner'].get_general_params(self)
            params.update(self.call_messenger_function('_get_partner_data', data))
            partner = self.env['res.partner'].create(params)
            messenger_partner = self.env['us.messenger.partner'].create({
                'bot_id': self.id,
                'partner_id': partner.id,
                'external_id': user_ref,
                'username': username
            })
            job.log('Partner and messenger_partner created: %s, %s' % (partner, messenger_partner))
        return messenger_partner, is_new_partner
    
    def create_channel(self, messenger_partner, data, job):
        '''Creating a communication channel for a partner.'''
        
        vals = self.env["discuss.channel"]._prepare_channel_vals(
            f'us_messenger_{self.bot_type}',
            self.channel_template % self._get_channel_name_vars(messenger_partner.partner_id), 
            messenger_partner.partner_id,
            messenger_partner,
            self,
        )
        channel = self.env["discuss.channel"].with_context(mail_create_nosubscribe=True).sudo().create(vals)

        job.log("Channel created: %s" % channel)
        return channel

    def _process_actions(self, messenger_partner, data, is_partner_created=False):
        self.ensure_one()
        partner_lang = self._get_partner_lang(data.get('request_data'))
        script = self.with_context(lang=partner_lang).script_id
        messenger_partner = messenger_partner.with_context(lang=partner_lang)

        # If first init return first step
        first_step = script.script_step_ids[:1] if is_partner_created else None
        steps_msg_kwargs = script._get_steps_kwargs(messenger_partner, data, step=first_step)
        return steps_msg_kwargs

    def _send_to_messenger(self, user_ref, **kwargs):
        return self.call_messenger_function('_send_to_messenger', user_ref, **kwargs)

    def _action_send_message(self, user_ref, message, document_message=None, messenger_partner=None):
        """
        Generic method to send message through messenger.
        
        :param user_ref: recipient identifier (chat_id, phone, etc.)
        :param message: mail.message record to send
        :param document_message: original document message for notification tracking
        :param messenger_partner: us.messenger.partner record for notification
        :return: dict with status and message_id
        """
        self.ensure_one()
        job = self.env['us.messenger.job'].create_trigger_job(
            self.id, 
            'Send message to ref: %s' % (user_ref) 
        )
        try:
            operator_id = self.operator_ids.filtered(lambda o: o.partner_id.id == message.author_id.id)
            author_name = operator_id.nickname if operator_id and operator_id.nickname else message.author_id.name
   
            message_html = edit_text_message(message.body, author_name, is_signature=self.is_add_operator_signature)
            job.log('Sending message: %s' % (message_html,))
            status = self.call_messenger_function(
                '_send_to_messenger', 
                user_ref, 
                text=message_html, 
                attachments=message.attachment_ids, 
                parse_mode='HTML',
                parent_msg_id=message.parent_id.external_messenger_id if message.parent_id else None,
            )
            job.log('Get status: %s' % (status,))
            if status.get('status') == "error":
                if document_message and messenger_partner:
                    self._create_messenger_notification(
                        document_message, messenger_partner, 'exception', str(status.get('message', ''))
                    )
                return status
            if status.get('external_message_id'):
                message.write({'external_messenger_id':str(status.get('external_message_id'))})
            
            if document_message and messenger_partner:
                self._create_messenger_notification(
                    document_message, messenger_partner, 'sent', ''
                )
            
            job.finish_job('done')
            return {'status': 'success'}
        except Exception as e:
            job.log('Error sending message: %s' % (str(e),), level=LOG_ERROR)
            job.finish_job('failed')
            if document_message and messenger_partner:
                self._create_messenger_notification(
                    document_message, messenger_partner, 'exception', str(e)
                )
            return {'status': 'error', 'message': str(e)}

    def _create_messenger_notification(self, document_message, messenger_partner, notification_status, failure_reason=''):
        """
        Create or update messenger notification for document message.
        
        :param document_message: mail.message record
        :param messenger_partner: us.messenger.partner record
        :param notification_status: 'ready', 'sent', 'exception', 'canceled'
        :param failure_reason: error message if failed
        """
        notification_type = self._get_notification_type()
        if not notification_type:
            return
        
        existing_notification = self.env['messenger.notification'].sudo().search([
            ('mail_message_id', '=', document_message.id),
            ('messenger_partner_id', '=', messenger_partner.id),
        ], limit=1)
        
        if existing_notification:
            existing_notification.write({
                'notification_status': notification_status,
                'failure_reason': failure_reason,
            })
        else:
            self.env['messenger.notification'].sudo().create({
                'mail_message_id': document_message.id,
                'messenger_partner_id': messenger_partner.id,
                'notification_type': notification_type,
                'notification_status': notification_status,
                'failure_reason': failure_reason,
            })
        
        document_message._notify_message_notification_update()

    def _get_notification_type(self):
        """
        Get notification type based on bot_type.
        Override in messenger-specific modules to return proper type.
        
        :return: notification_type string or False
        """
        return False

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def call_messenger_function(self, function_name, *args, **kwargs):
        method_name = f"_{self.bot_type}{function_name}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(*args, **kwargs)
        else:
            return {'status': 'error', 'message': 'Method %s not implemented' % method_name}

    def _get_messenger_image_path(self):
        """Return image path for messenger icon (to override in submodules)"""
        self.ensure_one()
        return False

    def _get_webhook_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        if 'https' not in base_url:
            scheme_from_odoo = request.httprequest.scheme
            if 'https' == scheme_from_odoo:
                base_url = base_url.replace('http', 'https')
                self.env['ir.config_parameter'].sudo().set_param('web.base.url', base_url)
        link = (
            self.website_path
            or ""
        )
        if base_url and link:
            path = "webhook/action-{webhook_type}/{link}".format(
                webhook_type=self.webhook_type, link=link
            )
            return urls.url_join(base_url, path)
        return ""

    def _get_channel_name_vars(self, partner):
        return {
            'name':partner.name, 
            'botname':self.name
        }

    def _get_partner_lang(self, data):
        lang = self.call_messenger_function('_get_partner_lang', data)
        locales = [locale[0] for locale in self.env['res.lang'].get_installed()]

        for item in locales:
            if lang.lower() in item.lower():
                return item

        return self.default_lang

    def _validate_webhook_url(self, webhook_url, requires_https=True):
        """Generic webhook URL validation."""
        if not webhook_url:
            return {'status': 'error', 'message': _("Webhook URL is not configured")}

        if requires_https and not webhook_url.startswith('https://'):
            return {'status': 'error', 'message': _("Webhook URL must use HTTPS protocol")}

        return {'status': 'success'}

    def _handle_api_exception(self, exception, operation_name):
        """Generic exception handling with logging."""
        import logging
        _logger = logging.getLogger(__name__)

        error_message = str(exception)
        _logger.error(f"{operation_name} failed for {self.bot_type}: {error_message}")

        return {'status': 'error', 'message': error_message}
