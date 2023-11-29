import logging
from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.tools import partition, collections, frozendict, lazy_property, image_process

USER_PRIVATE_FIELDS = []

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    customer = fields.Boolean(
       string='Customer',
    )

    fname = fields.Char()
    lname = fields.Char()
    partner_id = fields.Many2one(ondelete="cascade")
    role_id = fields.Selection(
        selection=[
                ("1", "Customer"),
                ("3", "Business Admin"),
            ],
        string="Registered As",
        default="3",
    )

    @ api.model
    def create(self, vals_list):  
        if 'role_id' in vals_list:
            if(vals_list['role_id'] == "1" ):
                groups_id = []  
                groups = self.env['res.groups'].search([('name','=','Customer Portal')])
                groups_id.append(groups.id)
                vals_list['customer'] = True
                vals_list["groups_id"] = [(6,0,groups_id)]
            elif(vals_list['role_id'] == "3"):
                groups_id = []  
                groups = self.env['res.groups'].search([('name','=','Business Admin')])
                groups_id.append(groups.id)
                vals_list["groups_id"] = [(6,0,groups_id)]
        if vals_list:
            vals_list.update({
                "g-recaptcha-response": "code@benja",
            })
        if vals_list["g-recaptcha-response"]:
            del vals_list["g-recaptcha-response"]
        
        user = super(ResUsers, self).create(vals_list) 
        if 'role_id' in vals_list:
            if vals_list['role_id'] == "1":
                user.write({
                    'customer':True
                })
                if user.partner_id:
                    user.partner_id.write({
                        'customer':True,
                        'company_ids':[(4,vals_list['company_id'])]
                    })
                    if 'phone' in vals_list:
                        user.partner_id.write({
                            'phone':vals_list['phone']
                        })         
        return user

    def write(self, values):
        if 'role_id' in values:
            if(values['role_id'] == "1" ):
                groups_id = []  
                groups = self.env['res.groups'].search([('name','=','Customer Portal')])
                groups_id.append(groups.id)
                values['customer'] = True
                values['employee'] = False
                values["groups_id"] = [(6,0,groups_id)]
    
            elif(values['role_id'] == "3"):
                groups_id = []  
                groups = self.env['res.groups'].search([('name','=','Business Admin')])
                groups_id.append(groups.id)

                values["groups_id"] = [(6,0,groups_id)]

        if values.get('active') and SUPERUSER_ID in self._ids:
            raise UserError(_("You cannot activate the superuser."))
        if values.get('active') == False and self._uid in self._ids:
            raise UserError(_("You cannot deactivate the user you're currently logged in as."))

        if values.get('active'):
            for user in self:
                if not user.active and not user.partner_id.active:
                    user.partner_id.toggle_active()
        if self == self.env.user:
            for key in list(values):
                if not (key in self.SELF_WRITEABLE_FIELDS or key.startswith('context_')):
                    break
            else:
                if 'company_id' in values:
                    if values['company_id'] not in self.env.user.company_ids.ids:
                        del values['company_id']
                # safe fields only, so we write as super-user to bypass access rights
                self = self.sudo().with_context(binary_field_real_user=self.env.user)

        res = super(ResUsers, self).write(values)

        if 'company_id' in values:
            if self.employee == True:
                self.employee_ids.unlink()
                self.employee_id.unlink()
                self.ensure_one()
                self.env['hr.employee'].create(dict(
                    name=self.name,
                    company_id=self.company_id.id,
                    **self.env['hr.employee']._sync_user(self)
                ))

        if 'role_id' in values:
            if values['role_id'] == "1":
                if self.partner_id:
                    self.partner_id.write({
                        'customer':True,
                        'employee':False,
                        'company_ids':[(4,self.company_id.id)]
                    })
                    self.employee_id.unlink()
            else:
                if self.partner_id:
                    self.partner_id.write({
                        'customer':True,
                        'employee':False,
                        'company_ids':[(4,self.company_id.id)]
                    })
                    self.employee_id.unlink()
    
        if 'company_id' in values:
            for user in self:
                # if partner is global we keep it that way
                if user.partner_id.company_id and user.partner_id.company_id.id != values['company_id']:
                    user.partner_id.write({'company_id': user.company_id.id})

        if 'company_id' in values or 'company_ids' in values:
            # Reset lazy properties `company` & `companies` on all envs
            # This is unlikely in a business code to change the company of a user and then do business stuff
            # but in case it happens this is handled.
            # e.g. `account_test_savepoint.py` `setup_company_data`, triggered by `test_account_invoice_report.py`
            for env in list(self.env.envs):
                if env.user in self:
                    lazy_property.reset_all(env)

        # clear caches linked to the users
        if self.ids and 'groups_id' in values:
            # DLE P139: Calling invalidate_cache on a new, well you lost everything as you wont be able to take it back from the cache
            # `test_00_equipment_multicompany_user`
            self.env['ir.model.access'].call_cache_clearing_methods()

        # per-method / per-model caches have been removed so the various
        # clear_cache/clear_caches methods pretty much just end up calling
        # Registry._clear_cache
        invalidation_fields = {
            'groups_id', 'active', 'lang', 'tz', 'company_id',
            *USER_PRIVATE_FIELDS,
            *self._get_session_token_fields()
        }
        if (invalidation_fields & values.keys()) or any(key.startswith('context_') for key in values):
            self.clear_caches()

        return res

    def unlink(self):     
        if SUPERUSER_ID in self.ids:
            raise UserError(_('You can not remove the admin user as it is used internally for resources created by Odoo (updates, module installation, ...)'))
        self.clear_caches()
        partner = self.partner_id
        partner.unlink()
        #return super(ResUsers, self).unlink()
    
    def action_reset_password(self):
        """ create signup token for each user, and send their signup url by email """
        if self.env.context.get('install_mode', False):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('auth_signup.reset_password_email')
        assert template._name == 'mail.template'

        website_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }

        template.write(template_values)
        acontext = {}
        acontext['website_base_url'] = website_base_url

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.with_context(acontext).send_mail(user.id, force_send=force_send, raise_exception=True)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)


