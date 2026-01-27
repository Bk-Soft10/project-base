import werkzeug

from odoo import http
from odoo.http import request, Response
import json


class Webhook(http.Controller):
    @http.route(
        [
            "/webhook/action-json/<path_or_xml_id_or_id>",
            "/webhook/action-json/<path_or_xml_id_or_id>/<path:path>",
        ],
        type="jsonrpc",
        auth="public",
        website=True,
        csrf=False,
    )
    def messenger_webhook_json(self, path_or_xml_id_or_id, **post):
        res = self._process_messenger_webhook(path_or_xml_id_or_id, **post)
        return res.data

    @http.route(
        [
            "/webhook/action-http/<path_or_xml_id_or_id>",
            "/webhook/action-http/<path_or_xml_id_or_id>/<path:path>",
        ],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def messenger_webhook_http(self, path_or_xml_id_or_id, **post):
        return self._process_messenger_webhook(path_or_xml_id_or_id, **post)

    def _process_messenger_webhook(self, path, **post):
        trigger = request.env["us.messenger.project"]
        action = None
        action = trigger.sudo().search(
            [
                ("website_path", "=", path),
            ],
            limit=1,
        )
        # run it, return only if we got a Response object
        if action:
            request_data = {}
            if 'application/json' in request.httprequest.content_type:
                request_data = json.loads(request.httprequest.data.decode("utf-8"))
            elif 'application/x-www-form-urlencoded' in request.httprequest.content_type:
                request_data = post

            if not request_data:
                return Response("Bad Request: No data received", status=400)

            action_res = action._process_message(request_data)
            if action_res.get('status') == 'success':
                return Response("OK", status=200, headers=[])
            else:
                return Response("Error", status=404, headers=[])

        return request.redirect("/")