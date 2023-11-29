# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import werkzeug

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.http import request, route

_logger = logging.getLogger(__name__)


class AuthSignupHomeExtension(AuthSignupHome):

    @route()
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        users = request.env['res.users'].sudo().search([])
        for key in list(qcontext):
            if key == 'name':
                for user in users:
                    if user.login == qcontext['login']:
                        names = user.name.split(' ')
                        qcontext.update({
                            'fname': names[0],
                        })
                        if user.phone:
                            qcontext.update({
                                'phone': user.phone,
                            })
                        if user.city:
                            qcontext.update({
                                'city': user.city,
                            })
                        if user.country_id.name:
                            qcontext.update({
                                'country': user.country_id.name,
                            })

                        if len(names) > 1:
                            qcontext.update({
                                'lname': names[1]
                            })
                        elif len(names) > 2:
                            qcontext.update({
                                'lname': names[1] + names[2]
                            })

        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return self.web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    assert login, _("No login provided.")
                    _logger.info(
                        "Password reset attempt for <%s> by user <%s> from %s",
                        login, request.env.user.login, request.httprequest.remote_addr)
                    request.env['res.users'].sudo().reset_password(login)
                    qcontext['message'] = _(
                        "An email has been sent with credentials to reset your password")
            except UserError as e:
                qcontext['error'] = e.args[0]
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)
        countries = request.env['res.country'].sudo().search([])
        qcontext.update({
            'countries': countries
        })
        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


    @http.route(website=True, auth="public")
    def web_login(self, redirect=None, *args, **kw):
        response = super(AuthSignupHomeExtension, self).web_login(redirect=redirect, *args, **kw)
        if not redirect and request.params['login_success']:
            if request.env['res.users'].browse(request.uid).has_group('base.group_user'):
                redirect = b'/web?' + request.httprequest.query_string
            else:
                redirect = '/my/leads'
            return http.redirect_with_hash(redirect)
        return response