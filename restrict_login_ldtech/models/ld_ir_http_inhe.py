# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

import werkzeug
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
import werkzeug.utils

from odoo import models, http, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.service import security

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        auth = 'none' if http.is_cors_preflight(request, endpoint) else endpoint.routing['auth']

        try:
            if request.session.uid is not None:
                if not security.check_session(request.session, request.env):
                    request.session.logout(keep_db=True)
                    request.env = api.Environment(request.env.cr, None, request.session.context)

                uid = request.session.uid
                user_pool = request.env['res.users'].with_user(
                    SUPERUSER_ID).browse(uid)
                def _update_user(u_sid, u_now, u_exp_date, u_uid):
                    """ Function for updating session details for the
                        corresponding user
                    """
                    if u_uid and u_exp_date and u_sid and u_now:
                        query = """update res_users set sid = '%s',
                                       last_update = '%s',exp_date = '%s',
                                       logged_in = 'TRUE' where id = %s
                                       """ % (u_sid, u_now, u_exp_date, u_uid)
                        request.env.cr.execute(query)

                sid = request.session.sid
                last_update = user_pool.last_update
                now = datetime.now()
                exp_date = datetime.now() + timedelta(minutes=45)

            getattr(cls, f'_auth_method_{auth}')()
        except (AccessDenied, http.SessionExpiredException, werkzeug.exceptions.HTTPException):
            raise
        except Exception:
            _logger.info("Exception during request Authentication.", exc_info=True)
            raise AccessDenied()
