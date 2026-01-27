from uuid import uuid4
from odoo import fields, models


class UsMessengerScriptAnswer(models.Model):
    _name = "us.messenger.script.answer"
    _description = "Messenger Script Answer"
    _order = "messenger_step_id, sequence, id"

    def get_default_answer_code(self):
        return str(uuid4())[:7]

    name = fields.Char('Answer Text', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1)
    messenger_step_id = fields.Many2one(
        'us.messenger.script.step',
        string='Step',
        required=True,
        index=True,
        ondelete='cascade',
    )
    next_step_id = fields.Many2one(
        comodel_name='us.messenger.script.step',
        string='Next Step',
    )
    script_id = fields.Many2one(
        related='messenger_step_id.script_id', 
        string='Bot Script',
    )
    answer_code = fields.Char(
        string='Answer Code',
        default=lambda self: self.get_default_answer_code(),
        copy=False,
        readonly=True,
        required=True,
    )
