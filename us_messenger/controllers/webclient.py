from odoo.http import request, route
from odoo.addons.mail.controllers.webclient import WebclientController
from odoo.addons.mail.tools.discuss import Store


class WebClient(WebclientController):
    @classmethod
    def _process_request_for_internal_user(self, store: Store, name, params):
        super()._process_request_for_internal_user(store, name, params)
        store.add(request.env["us.messenger.project"].sudo().search([]), ["are_you_inside", "name"])