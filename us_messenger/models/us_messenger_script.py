from collections import deque

from odoo import api, Command, models, fields, _
from odoo.exceptions import ValidationError


class UsMessengerScript(models.Model):
    _name = "us.messenger.script"
    _inherit = "image.mixin"
    _description = "Messenger Script"

    name = fields.Char('Script Name', required=True)
    image_1920 = fields.Image(related='operator_partner_id.image_1920', readonly=False)
    project_ids = fields.One2many(
        comodel_name='us.messenger.project', 
        inverse_name='script_id', 
        string='Bot',
    )
    bot_type = fields.Selection(
        selection=[],
        string='Bot Type',
        required=True,
    )
    script_step_ids = fields.One2many(
        comodel_name='us.messenger.script.step',
        inverse_name='script_id',
        string='Script Steps',
        copy=True,
    )
    available_question_selection = fields.Boolean(
        string='Available Question Selection',
        compute='_compute_available_question_selection',
        store=True,
    )
    operator_partner_id = fields.Many2one(
        comodel_name='res.partner', 
        string='Bot Operator',
        ondelete='restrict', 
        required=True, 
        copy=False, 
        index=True
    )

    # Common phrases for some bot steps
    share_phone_btn_text = fields.Text(
        string='Share Phone Button Text',
        translate=True,
        default='Share phone number',
        required=True,
        help='In some messengers, the phone number is transferred by pressing a button. '
       'This text will be displayed on the button.',
    )
    
    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
         
    @api.depends('bot_type')
    def _compute_available_question_selection(self):
        for record in self:
            record.available_question_selection = record._get_available_question_selection()

    # -------------------------------------------------------------------------
    # CONSTRAINT METHODS
    # -------------------------------------------------------------------------

    @api.constrains("script_step_ids")
    def _check_question_selection(self):
        for step in self.script_step_ids:
            if "question_selection" in step.step_type_code and not step.answer_ids:
                raise ValidationError(self.env._("Step of type 'Question' must have answers."))
    
    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.onchange("script_step_ids")
    def _onchange_script_step_ids(self):
        for step in self.script_step_ids:
            if "question_selection" not in step.step_type_code and step.answer_ids:
                step.answer_ids = [Command.clear()]
    
    # -------------------------------------------------------------------------
    # LOW-LEVEL METHODS
    # -------------------------------------------------------------------------

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        return [dict(vals, name=self.env._("%s (copy)", script.name)) for script, vals in zip(self, vals_list)]

    def copy(self, default=None):
        """Properly copy next_step_id in steps and step answers.

            Old steps:
            STEP ID     NEXT STEP ID
            1           2
            2           4
            3           4
            4           1
            
            New steps:
            STEP ID     NEXT STEP ID
            5           id = orig_clone_steps_map[old_step.next_step_id]
            6           8
            7           8
            8           5

            orig_clone_steps_map = {
                1: 5,
                2: 6,
                3: 7,
                4: 8,
            }
        """
        default = default or {}
        new_scripts = super().copy(default=default)

        for old_script, new_script in zip(self, new_scripts):
            original_steps = old_script.script_step_ids.sorted()
            clone_steps = new_script.script_step_ids.sorted()
            
            orig_clone_steps_map = {}

            for clone_step, original_step in zip(clone_steps, original_steps):
                orig_clone_steps_map[original_step] = clone_step.id

            for clone_step, original_step in zip(clone_steps, original_steps):
                if original_step.next_step_id:
                    clone_step.write({
                        'next_step_id': orig_clone_steps_map[original_step.next_step_id]
                    })
                if original_steps.answer_ids:
                    for clone_answer, original_answer in zip(clone_step.answer_ids.sorted(), original_step.answer_ids.sorted()):
                        if original_answer.next_step_id:
                            clone_answer.write({
                                'next_step_id': orig_clone_steps_map[original_answer.next_step_id]
                            })

        return new_scripts

    @api.model_create_multi
    def create(self, vals_list):
        operator_partners_values = [{
            'name': vals['name'],
            'image_1920': vals.get('image_1920', False),
            'active': False,
        } for vals in vals_list if 'operator_partner_id' not in vals and 'name' in vals]

        operator_partners = self.env['res.partner'].create(operator_partners_values)

        for vals, partner in zip(
            [vals for vals in vals_list if 'operator_partner_id' not in vals and 'name' in vals],
            operator_partners
        ):
            vals['operator_partner_id'] = partner.id

        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)

        if 'name' in vals:
            self.operator_partner_id.write({'name': vals['name']})

        return res
    
    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _recompute_step_flow(self):
        """ Updates the next_step_id links for all script steps """
        for script in self:
            steps = script.script_step_ids.sorted('sequence')

            for index, step in enumerate(steps):
                if step.is_manual_next_step:
                    continue

                target_next = steps[index + 1] if index + 1 < len(steps) else False

                if step.next_step_id != target_next:
                    step.with_context(skip_next_step_recompute=True).write({'next_step_id': target_next})

    def _get_steps_kwargs(self, messenger_partner, message_data, step=None):
        """ Returns the steps to be performed.

        Find current step in the next priority:
            1. The user executed the command
            2. The user's current step
            3. The bot's first step, if the user initiated interaction with the bot
        """
        self.ensure_one()
        message_qeque = deque()

        next_step, command_args = self._find_step_by_command(message_data.get("body")) 
        current_step = messenger_partner.current_step_id
        
        # If current step is forward operator ignore any commands
        if current_step and current_step.is_forward_operator:
            next_step = None

        if not next_step and current_step:
            # Check whether the user's current step is in the list of steps for the current script. 
            # There may be cases where scripts are replaced in the bot or a step is deleted.
            if current_step and current_step.id not in self.script_step_ids.ids:
                current_step = self.script_step_ids[:1]
            if step_kwargs := current_step._process_answer(messenger_partner, message_data):
                message_qeque.append(step_kwargs)

            # If the next step has not changed, exit the method. 
            if current_step.id == messenger_partner.current_step_id.id:
                return message_qeque
            else:
                next_step = messenger_partner.current_step_id

        if not next_step and step:
            next_step = step
        
        # Get step types that can be executed togather
        one_action_steps = self.env['us.messenger.script.step']._get_steps_without_answer()

        steps_to_process = []
        while next_step:
            step_kwargs = next_step._process_step(messenger_partner, command_args)
            message_qeque.append(step_kwargs)

            # Fetch next step
            if next_step.step_type_code not in one_action_steps:
                messenger_partner.write({'current_step_id': next_step.id})
                break
            steps_to_process.append(next_step.id)
            next_step = next_step._fetch_next_step(messenger_partner)

            # Prevent looping, exit the loop if the step tries to be added a second time
            if next_step and next_step.id in steps_to_process:
                break
        return message_qeque
    
    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _find_step_by_command(self, message_body):
        """Find the step if the message contained the command"""
        self.ensure_one()

        command, command_args = self._extract_step_command(message_body)
        if not command:
            return None, None
        command_step = self.env['us.messenger.script.step'].search(
            [
                ('script_id', '=', self.id), 
                ('step_command', '=', command)
            ], 
            limit=1,
        )
        return command_step, command_args

    def _get_available_question_selection(self):
        """To override"""
        return False

    def _extract_step_command(self, message_body):
        text = (message_body or "").strip()
        if not text.startswith("/"):
            return None, None

        parts = text.split(maxsplit=1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else None

        return command, args
    