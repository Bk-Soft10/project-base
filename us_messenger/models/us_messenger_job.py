from odoo import api, fields, models
from odoo.tools.translate import _


class UsMessengerJob(models.Model):
    _name = "us.messenger.job"
    _description = "Messenger Job"
    _order = "id desc"

    project_id = fields.Many2one(
        "us.messenger.project", readonly=True
    )
    log_ids = fields.One2many("ir.logging", "messenger_job_id", readonly=True)
    log_count = fields.Integer(compute="_compute_log_count")
    function = fields.Char(string="Task Function")
    state = fields.Selection(
        [('started', 'Started'),('done', 'Done'), ('failed', 'Failed')],
        string='State', readonly=True
    )

    @api.depends("log_ids")
    def _compute_log_count(self):
        for r in self:
            r.log_count = len(r.log_ids)

    def create_trigger_job(self, project_id, function):
        return self.create(
            {
                "project_id": project_id,
                "function": function,
                "state": 'started'
            }
        )
    
    def finish_job(self, state):
        self.ensure_one()
        self.log('Job finished with state %s' % (state,))
        self.write({'state':state})
    
    def log(self, message, level='info', name='Log', log_type='server', traceback=None):
        """Create a log entry for this job."""
        self.ensure_one()
        if traceback:
            message = f"{message}\n\nTraceback:\n{traceback}"
        log_vals = {
            'create_date': fields.Datetime.now(),
            'create_uid': self.env.uid,
            'type': log_type,
            'dbname': self.env.cr.dbname,
            'name': name,
            'level': level,
            'message': message,
            'path': 'us.messenger.job',
            'line': self.id,
            'func': self.function,
            'messenger_job_id': self.id,
        }
        return self.env['ir.logging'].sudo().create(log_vals)

    @api.model
    def _gc_messenger_jobs(self):
        """Deletes entries created more than a week ago."""
        date_limit = fields.Datetime.subtract(fields.Datetime.now(), days=7)
        jobs_to_delete = self.sudo().search([('create_date', '<', date_limit)])
    
        if jobs_to_delete:
            jobs_to_delete.sudo().unlink()
