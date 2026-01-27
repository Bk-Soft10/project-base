import base64
import random

from markupsafe import Markup

from odoo import api, fields, models, Command, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.addons.mail.tools.discuss import Store
from odoo.tools import html2plaintext

ODOO_CHANNEL_TYPES = ["chat", "channel", "livechat", "group"]


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    messenger_operator_id = fields.Many2one("res.partner", string="Operator")
    messenger_partner_id = fields.Many2one(
        comodel_name="us.messenger.partner", 
        string="Messenger partner", 
        ondelete="cascade",
    )
    messenger_client_partner_id = fields.Many2one(
        comodel_name='res.partner', 
        string='Client partner', 
        related='messenger_partner_id.partner_id',
    )
    us_messenger_project_id = fields.Many2one(
        comodel_name='us.messenger.project', 
        string='Messenger Project', 
        compute='_compute_us_messenger_project_id',
        store=True,
    )
    messenger_status = fields.Selection(
        selection=[
            ("in_progress", "In progress"),
            ("waiting_customer", "Waiting for customer"),
            ("need_help", "Looking for help"),
            ("end_session", "End session"), 
            ("without_operator", "Without operator")
        ],
        string='Messenger status',
        groups="base.group_user",
    )
    last_end_session = fields.Datetime('Last end')
    messenger_note = fields.Html(
        "Messenger Note",
        sanitize_style=True,
        groups="base.group_user",
        help="Note about the customer",
    )
    lead_ids = fields.One2many(
        "crm.lead",
        "us_messenger_channel_id",
        string="Leads",
        groups="sales_team.group_sale_salesman",
    )

    _unique_messenger_partner = models.Constraint('unique(messenger_partner_id)', 'messenger_partner_id must be unique to ensure one2one relationship')

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('messenger_partner_id')
    def _compute_us_messenger_project_id(self):
        for channel in self:
            channel.us_messenger_project_id = channel.messenger_partner_id.bot_id

    # -------------------------------------------------------------------------
    # LOW-LEVEL METHODS
    # -------------------------------------------------------------------------

    def write(self, vals):
        result = super().write(vals)
        # Notify all users about status change via bus for real-time updates
        if "messenger_status" in vals:
            if vals['messenger_status'] == 'end_session':
                self.write({'last_end_session': fields.Datetime.now()})
            for channel in self:
                if channel.messenger_partner_id:
                    Store(bus_channel=channel).add(channel, ["messenger_status"]).bus_send()
        return result

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _messenger_forward_to_operator(self):
        self.ensure_one()

        bot = self.us_messenger_project_id
        automatic_operator_selection = bool(self.env['ir.config_parameter'].sudo().get_param('us_messenger.auto_operator_selection', False))
        operators_to_add = self.env['res.partner']
        messenger_operator_id = None
        channel_status = 'without_operator'

        # If we find an available operator, we add it to the channel.
        if automatic_operator_selection and (operator := self._get_messenger_operator(bot)):
            operators_to_add += operator.partner_id
            messenger_operator_id = operator.partner_id.id
            channel_status = 'in_progress'
        
        # Otherwise, we proceed to add all operators to channel.
        elif bot.operator_ids:
            operators_to_add += bot.operator_ids.partner_id
            odoobot = self.env.ref('base.partner_root')
            messenger_operator_id = None if automatic_operator_selection else odoobot.id

        self.add_members(operators_to_add.ids, post_joined_message=False)
        self.write({
            'messenger_operator_id': messenger_operator_id,
            'messenger_status': channel_status, 
        })
        self._broadcast(operators_to_add.ids)
        self.channel_pin(pinned=False)

    def _get_messenger_less_active_operator(self, operator_statuses, operators, max_channels=5):
        """ Retrieve the most available operator based on the following criteria:
        - Lower priority operators are preferred (priority 1 before priority 2)
        - Higher priority operators are selected only when all lower priority 
          operators have >= max_channels active chats
        - Among operators with same priority: select one with fewest active chats
        - Prefer operators not in a call

        :param operator_statuses: list of dictionaries containing the operator's
            id, the number of active chats, priority and a boolean indicating 
            if the operator is in a call.
        :param operators: recordset of :class:`UsMessengerOperator` operators to choose from.
        :param max_channels: maximum number of channels before considering next priority level.
        :return: the :class:`UsMessengerOperator` record for the chosen operator
        """
        if not operators:
            return False

        operator_statuses = [
            s for s in operator_statuses if s['partner_id'] in set(operators.partner_id.ids)
        ]
        
        if not operator_statuses:
            return random.choice(operators)

        priorities = sorted(set(s['priority'] for s in operator_statuses))
        
        for priority in priorities:
            priority_statuses = [s for s in operator_statuses if s['priority'] == priority]
            available_in_priority = [s for s in priority_statuses if s['channel_count'] < max_channels]
            
            if available_in_priority:
                available_in_priority.sort(key=lambda s: (s['channel_count'], s['in_call']))
                best_status = available_in_priority[0]
                best_status_op_partner_ids = {
                    s['partner_id']
                    for s in available_in_priority
                    if (s['channel_count'], s['in_call']) == (best_status['channel_count'], best_status['in_call'])
                }
                candidates = operators.filtered(lambda o: o.partner_id.id in best_status_op_partner_ids)
                return random.choice(candidates)
        
        best_status = min(operator_statuses, key=lambda s: (s['channel_count'], s['in_call']))
        candidates = operators.filtered(lambda o: o.partner_id.id == best_status['partner_id'])
        return candidates[0] if candidates else random.choice(operators)

    def _get_messenger_operator(self, bot_id):
        """ Return the most suitable messenger operator for a messenger session.
    
        The selection logic follows these priority levels:
        1. Availability: Only operators with an 'im_status' of 'online' or 'away' are considered.
        2. Priority-based selection: Lower priority operators (priority 1) are preferred.
           Higher priority operators (priority 2, 3, etc.) are selected only when all 
           lower priority operators have >= 5 active chats.
        3. Workload Balancing: Among operators with same priority, the system selects 
           the one with the fewest active chats and prioritizes those not currently 
           engaged in an RTC (voice/video) session.

        A messenger channel is considered 'active' if:
        - It matches the 'us_messenger_%' type.
        - It was created within the last 24 hours.
        - It has received at least one message within the last 30 minutes.

        :param bot_id: The bot through which the visitor is communicating.
        
        :return: The selected messenger operator record or False if no one is available.
        :rtype: us.messenger.operator or False
        """
        if not bot_id:
            return False
        
        self.env["discuss.channel.rtc.session"].sudo()._gc_inactive_sessions()
        available_operator_ids = bot_id.operator_ids.filtered(
            lambda o: o.user_id.im_status in ['online', 'away'] and o.partner_id.id != self.messenger_client_partner_id.id
        )
        if not available_operator_ids:
            return False
        self.env.cr.execute("""
            WITH operator_rtc_session AS (
                SELECT COUNT(DISTINCT s.id) as nbr, member.partner_id as partner_id
                FROM discuss_channel_rtc_session s
                JOIN discuss_channel_member member ON (member.id = s.channel_member_id)
            GROUP BY member.partner_id
            ),
            requested_operators AS (
                SELECT partner_id, priority 
                FROM us_messenger_operator 
                WHERE id IN %s
            )
            SELECT 
                ro.partner_id,
                COUNT(DISTINCT c.id) as channel_count,
                COALESCE(rtc.nbr, 0) > 0 as in_call,
                ro.priority
            FROM requested_operators ro
            LEFT JOIN discuss_channel c ON c.messenger_operator_id = ro.partner_id 
                AND c.channel_type LIKE 'us_messenger_%%'
                AND c.create_date > (NOW() AT TIME ZONE 'UTC' - INTERVAL '24 hours')
                AND EXISTS (
                    SELECT 1 FROM mail_message m 
                    WHERE m.res_id = c.id 
                    AND m.model = 'discuss.channel' 
                    AND m.create_date > (NOW() AT TIME ZONE 'UTC' - INTERVAL '30 minutes')
                    LIMIT 1
                )
            LEFT JOIN operator_rtc_session rtc ON rtc.partner_id = ro.partner_id
            GROUP BY ro.partner_id, ro.priority, rtc.nbr
            ORDER BY 
                ro.priority ASC, 
                (COUNT(DISTINCT c.id) < 5 AND rtc.nbr IS NULL) DESC,
                COUNT(DISTINCT c.id) ASC,
                rtc.nbr IS NULL DESC""", (tuple(available_operator_ids.ids),)
            )

        operator_statuses = self.env.cr.dictfetchall()
        return self._get_messenger_less_active_operator(operator_statuses, available_operator_ids)  

    def _get_allowed_message_params(self):
        return super()._get_allowed_message_params() | {"document_message_id", "external_messenger_id"}

    def message_post(self, **kwargs):
        '''Override'''
        message = super(DiscussChannel, self).message_post(**kwargs)
        messenger_partner = self.sudo().messenger_partner_id
        if message.message_type == 'comment' and messenger_partner and message.author_id.id not in (messenger_partner.partner_id.id, self.env.user.browse(SUPERUSER_ID).partner_id.id, messenger_partner.bot_id.script_id.operator_partner_id.id):
            document_message_id = kwargs.get('document_message_id')
            document_message = self.env['mail.message'].browse(document_message_id) if document_message_id else None
            
            status = messenger_partner.bot_id._action_send_message(
                messenger_partner.external_id, 
                message,
                document_message=document_message,
                messenger_partner=messenger_partner,
            )
            if status.get('status', '') == 'error':
                self.message_post(
                    body=status.get('message'),
                    author_id=self.env.user.browse(SUPERUSER_ID).partner_id.id, 
                    message_type="comment", 
                    subtype_xmlid="mail.mt_comment"
                )

        return message

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    @api.model
    def _prepare_channel_vals(
            self, channel_type, channel_name, partner, messenger_partner, bot
    ):
        return {
            "channel_partner_ids":  [(4, partner.id)],
            "group_public_id": None,
            "channel_type": channel_type,
            "messenger_partner_id": messenger_partner.id,
            "name": channel_name,
        }

    def _get_messenger_types(self):
        # Override to add messenger types for channels
        return []

    # -------------------------------------------------------------------------
    # LEAD CREATION
    # -------------------------------------------------------------------------

    def execute_command_messenger_lead(self, **kwargs):
        """Create a lead from messenger channel using /messenger_lead command."""
        key = kwargs['body']
        lead_command = "/messenger_lead"
        if key.strip() == lead_command:
            msg = _(
                "Create a new lead with: "
                "%(pre_start)s%(lead_command)s %(i_start)slead title%(i_end)s%(pre_end)s",
                lead_command=lead_command,
                pre_start=Markup("<pre>"),
                pre_end=Markup("</pre>"),
                i_start=Markup("<i>"),
                i_end=Markup("</i>"),
            )
        else:
            lead = self._convert_messenger_to_lead(self.env.user.partner_id, key)
            msg = _("Created a new lead: %s", lead._get_html_link())
            store = Store(bus_channel=self)
            store.add(lead, ["id", "name"])
            store.add(self, [Store.Many("lead_ids", ["id", "name"])])
            store.bus_send()
        self.env.user._bus_send_transient_message(self, msg)

    def _convert_messenger_to_lead(self, partner, key):
        """Create a lead from messenger channel /messenger_lead command.
        
        :param partner: internal user partner (operator) that created the lead
        :param key: operator input in chat ('/messenger_lead Lead about Product')
        :return: crm.lead record
        """
        customers = self.env['res.partner']
        for customer in self.with_context(active_test=False).channel_partner_ids.filtered(
            lambda p: p != partner and p.partner_share
        ):
            if customer.is_public:
                customers = self.env['res.partner']
                break
            else:
                customers |= customer

        utm_source = self.env.ref('us_messenger.utm_source_messenger', raise_if_not_found=False)
        lead_name = html2plaintext(key[len("/messenger_lead"):].strip())
        return self.env['crm.lead'].create({
            'us_messenger_channel_id': self.id,
            'name': lead_name or _('Messenger Lead'),
            'partner_id': customers[0].id if customers else False,
            'user_id': False,
            'team_id': False,
            'description': self._get_messenger_channel_history(),
            'referred': partner.name,
            'source_id': utm_source and utm_source.id,
        })

    def _get_messenger_channel_history(self):
        """Get channel message history for lead description."""
        messages = self.env['mail.message'].search([
            ('model', '=', 'discuss.channel'),
            ('res_id', '=', self.id),
        ], order='id desc', limit=100)
        
        parts = []
        for msg in reversed(messages):
            author = msg.author_id.name or _('Unknown')
            body = html2plaintext(msg.body) if msg.body else ''
            if body:
                parts.append(Markup("<strong>%s:</strong> %s<br/>") % (author, body))
        
        return Markup("").join(parts)

    def _to_store_defaults(self, target):
        is_messenger_channel = lambda channel: channel.channel_type.startswith('us_messenger_')
        return super()._to_store_defaults(target) + [
            Store.One(
                "us_messenger_project_id", 
                ["id", "name", "are_you_inside"], 
                predicate=is_messenger_channel, 
                sudo=True,
            ),
            Store.One(
                "messenger_client_partner_id",
                ["id", "name", "display_name"],
                predicate=is_messenger_channel,
            ),
            Store.One("messenger_operator_id", predicate=is_messenger_channel),
            Store.Attr("messenger_status", predicate=is_messenger_channel),
            Store.Attr("messenger_note", predicate=is_messenger_channel),
            Store.Many("lead_ids", ["id", "name"], predicate=is_messenger_channel, sudo=True),
        ]
