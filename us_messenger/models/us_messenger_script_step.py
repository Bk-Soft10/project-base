from odoo import api, fields, models, _
from odoo.tools import email_normalize


class UsMessenegerScriptStepType(models.Model):
    _name = "us.messenger.script.step.type"
    _description = "Messenger Script Step Type"

    name = fields.Char(string='Type Name', required=True)
    bot_type = fields.Selection(
        selection=[
            ('all_bots', 'All Bots'),
        ],
        string='Bot Type',
        default='all_bots',
        required=True,
    )
    step_type = fields.Char(string='Step Type', required=True)

    _unique_step_type = models.Constraint(
        'unique(step_type)',
        'This step type already exists in the system. '
    )


class UsMessenegerScriptStep(models.Model):
    _name = "us.messenger.script.step"
    _description = "Messenger Script Step"
    _order = "sequence, id"

    name = fields.Char(string='Script Name',  compute='_compute_name')
    message = fields.Text(string='Message', required=True, translate=True)
    sequence = fields.Integer(string='Sequence')
    script_id = fields.Many2one('us.messenger.script', string='Bot Script', ondelete='cascade')
    bot_type = fields.Selection('Bot Type', related='script_id.bot_type')
    step_command = fields.Char(string='Command', help='This step will only be performed if the corresponding command is received.')
    step_type_id = fields.Many2one(
        comodel_name='us.messenger.script.step.type',
        string='Step Type',
        required=True,
    )
    step_type_code = fields.Char('Step Type Code', related='step_type_id.step_type')
    available_question_selection = fields.Boolean(related='script_id.available_question_selection')
    success_message = fields.Text(
        'Success Message',
        translate=True,
        default='Thank you, your reply has been saved successfully.',
        help='Message if the step was successful',
    )
    fault_message = fields.Text(
        'Fault Message',
        translate=True,
        default='Incorrect data entered, please try again.',
        help='Message about unsuccessful execution of a step, for example, '
        'if no operator was found, display the message no available operators found.',
    )
    show_success_message = fields.Boolean(
        string='Show Success Message', 
        compute="_compute_show_success_message", 
        store=True
    )
    show_fault_message = fields.Boolean(
        string='Show Fault Message', 
        compute="_compute_show_fault_message", 
        store=True
    )
    answer_ids = fields.One2many(
        comodel_name='us.messenger.script.answer', 
        inverse_name='messenger_step_id',
        copy=True,
        string='Answers',
    )
    is_forward_operator = fields.Boolean(compute='_compute_is_forward_operator')
    apply_for_partner = fields.Boolean(
        'Apply For Partner', 
        default=False,
        help='Automatically assign the specified data to the current partner. If disabled, data will only be stored in the channel.',
    )
    next_step_id = fields.Many2one(
        comodel_name='us.messenger.script.step',
        string='Next Step',
    )
    is_manual_next_step = fields.Boolean(
        string="Should Not Recompute Next Step",
        default=False,
        help="When a user changes the order of steps or creates new steps in a script, the steps are recalculated to automatically determine the next step for each step. "
        "If this field is enabled, the next step will not be determined for the current step.",
    )

    _unique_step_command = models.Constraint(
        'unique(script_id, step_command)',
        'This command already exists in this script.'
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends("sequence", "script_id")
    @api.depends_context('lang')
    def _compute_name(self):
        for step in self:     
            step.name = self.env._(
                "%(msg)s %(dots)s",
                msg=step.message[:30],
                dots="..." if len(step.message) > 30 else "",
            )

    @api.depends('step_type_code')
    def _compute_show_success_message(self):
        for record in self:
            record.show_success_message = True if record.step_type_code in record._get_success_msg_step_types() else False

    @api.depends('step_type_code')
    def _compute_show_fault_message(self):
        for record in self:
            record.show_fault_message = True if record.step_type_code in record._get_fault_msg_step_types() else False

    @api.depends("step_type_id")
    def _compute_is_forward_operator(self):
        for step in self:
            step.is_forward_operator = step.step_type_id.step_type == "forward_operator"

    # -------------------------------------------------------------------------
    # LOW-LEVEL METHODS
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'next_step_id' in vals and 'is_manual_next_step' not in vals:
                vals['is_manual_next_step'] = bool(vals.get('next_step_id'))

        vals_by_bot_id = {}
        for vals in vals_list:
            bot_id = vals.get('script_id')
            if bot_id:
                step_values = vals_by_bot_id.get(bot_id, [])
                step_values.append(vals)
                vals_by_bot_id[bot_id] = step_values

        read_group_results = self.env['us.messenger.script.step']._read_group(
            [('script_id', 'in', list(vals_by_bot_id))],
            ['script_id'],
            ['sequence:max'],
        )
        max_sequence_by_chatbot = {
            chatbot_script.id: sequence
            for chatbot_script, sequence in read_group_results
        }

        for chatbot_id, step_vals in vals_by_bot_id.items():
            current_sequence = 0
            if chatbot_id in max_sequence_by_chatbot:
                current_sequence = max_sequence_by_chatbot[chatbot_id] + 1

            for vals in step_vals:
                if 'sequence' in vals:
                    current_sequence = vals.get('sequence')
                else:
                    vals['sequence'] = current_sequence
                    current_sequence += 1

        records = super().create(vals_list)
        records.mapped('script_id')._recompute_step_flow()
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_next_step_recompute'):
            if 'sequence' in vals or 'script_id' in vals:
                self.mapped('script_id')._recompute_step_flow()
        return res

    def unlink(self):
        scripts = self.mapped('script_id')
        res = super().unlink()
        scripts._recompute_step_flow()
        return res

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _process_answer(self, messenger_partner, message_data):
        """
        Processing the answer consists of three stages:
            1. Validating the response
            2. Searching for the next step
            3. Building the response message

        The response message must contain a dictionary with two keys:
            1. `channel_msg` contains mail.message or None
            2. `messenger_msg` contains kwargs for sending a message to the messenger
        If the response at this step needs to be skipped, a dictionary with empty values 
        is returned dict(channel_msg=None,messenger_msg=dict())

        :param us.messenger.partner: current messenger partner
        :param message_data: message data from messenger
        :return dict: message kwargs
        """
        self.ensure_one()
        answer_result = self._validate_answer(messenger_partner, message_data)
       
        # Change step only if answer is valid
        if answer_result.get('is_valid'):
            # If step process email or phone, we need assign this data 
            # for current partner if field apply_for_partner is enabled
            if self.apply_for_partner:
                self._apply_partner_data(messenger_partner, message_data)

            # For question_selection step type fetch next step in answer if exists
            if answer_next_step := answer_result.get('next_step'):
                next_step = answer_next_step
            else:
                next_step = self._fetch_next_step(messenger_partner)

            messenger_partner.write({'current_step_id': next_step.id if next_step else None})

        return self._build_message_kwargs(answer_result.get('message'), messenger_partner, message_data, is_answer=True, **answer_result)

    def _validate_answer(self, messenger_partner, message_data):
        """Validate data in answer.

        Always return a dictionary with such keys:
            1. message: str message response
            2. is_valid: вoolean flag that determines a valid answer
        Optional key:
            1. next_step: for question_selection type define next_step for answer
        """
        res = {
            'message': self.success_message if self.step_type_code not in self._get_steps_without_answer() else None,
            'is_valid': True,
        }
        if self.step_type_code == 'question_email' and not email_normalize(message_data.get('body')):
            res.update({
                'message': self.fault_message or _('Incorrect data entered, please try again.'),
                'is_valid': False,
            })
        elif self.step_type_code == 'forward_operator':
            res.update({
                'message': None,
                'is_valid': False,
            })
        
        return res
    
    def _fetch_next_step(self, messenger_partner):
        """Fetch next step after current step."""
        self.ensure_one()
        next_step = self.next_step_id
        # Skip step if partner already has email or phone
        if (
            next_step and next_step.apply_for_partner
            and (next_step.step_type_code == 'question_email' and messenger_partner.partner_id.email 
            or next_step.step_type_code == 'question_phone' and messenger_partner.partner_id.phone)
        ):
            return next_step._fetch_next_step(messenger_partner)
        return next_step 
    
    def _apply_partner_data(self, messenger_partner, message_data):
        if self.step_type_code == 'question_email':
            messenger_partner.partner_id.write({'email': message_data.get('body')})
            
        elif self.step_type_code == 'question_phone':
            messenger_partner.partner_id.write({'phone': message_data.get('body')})
            messenger_partner.link_child_parent()

    def _build_message_kwargs(self, msg, messenger_partner, message_data=None, attachment=None, is_answer=False, **kwargs):
        """To Override"""
        return dict(channel_msg=None, messenger_msg=dict())

    def _process_step(self, messenger_partner, command_args=None):
        if self.step_type_code == 'forward_operator':
            messenger_partner.channel_id._messenger_forward_to_operator()
            
        return self._build_message_kwargs(self.message, messenger_partner)

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _get_success_msg_step_types(self):
        return ['question_phone', 'question_email', 'free_input_single']

    def _get_fault_msg_step_types(self):
        return ['question_phone', 'question_email']

    @api.model
    def _get_steps_without_answer(self):
        """Steps that do not require an answer."""
        return ['text']
