import base64
import logging
import json
from xml import dom
import werkzeug
from odoo.exceptions import AccessError
from datetime import datetime
from odoo import _
import odoo.http as http
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.web.controllers.main import Home                
_logger = logging.getLogger(__name__)


class Website(Home):
    @http.route(website=True, auth="public")
    def web_login(self, redirect=None, *args, **kw):
        response = super(Website, self).web_login(redirect=redirect, *args, **kw)
        if not redirect and request.params['login_success']:
            if request.env['res.users'].browse(request.uid).has_group('base.group_user'):
                redirect = b'/web?' + request.httprequest.query_string
            else:
                redirect = '/my/leads'
            return http.redirect_with_hash(redirect)
        return response
            

class CustomerPortal(CustomerPortal):

    @route(["/my/leads", "/my/leads/page/<int:page>"],type="http",auth="user",website=True,)
    def portal_my_leads(
        self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, noFilter=True, **kw
    ):
        values = self._prepare_portal_layout_values()
        CrmLead = request.env["crm.lead"]
        partner = request.env.user.partner_id
        domain = [("partner_id", "child_of", partner.id)]

        searchbar_sortings = {
            "date": {"label": _("Newest"), "order": "create_date desc"},
            "name": {"label": _("Name"), "order": "name"},
            "stage": {"label": _("Stage"), "order": "stage_id"},
            "update": {
                "label": _("Last Stage Update"),
                "order": "last_stage_update desc",
            },
        }

        searchbar_filters = {"all": {"label": _("All"), "domain": []}}
        for stage in request.env["crm.lead.stage"].search([]):
            searchbar_filters.update({
                    str(stage.id): {
                        "label": stage.name,
                        "domain": [("stage_id", "=", stage.id)],
                    }
                }
            )

        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        # default filter by value
        if not filterby:
            filterby = "all"
            noFilter = False
        
        try:
            domain += searchbar_filters[filterby]["domain"]
        except KeyError:
            filterby = "all"
            domain += searchbar_filters[filterby]["domain"]
        # count for pager
        lead_count = True
        # pager
        pager = portal_pager(
            url="/my/leads",
            url_args={},
            total=lead_count,
            page=page,
            step=self._items_per_page,
        )
        
        new_lead_count = 0
        progress_lead_count = 0
        done_lead_count = 0
        cancelled_lead_count = 0
        
        leads = CrmLead.sudo().search(
            [("email_from", "=", partner.email)])
        
        if leads:
            lead_count = True

        total_count = lead_count
        for lead in leads:
            if lead.stage_id.name == "New":
                new_lead_count += 1
            elif (lead.stage_id.name == "Qualified") or (lead.stage_id.name == "Proposition"):
                progress_lead_count += 1
            elif lead.stage_id.name == "Won":
                done_lead_count += 1

        if filterby == "all":
            leads = CrmLead.sudo().search(
                [("email_from", "=", partner.email)])
            if not leads:
                leads = False
            if  leads == False:
                total_count = False

        elif filterby == "1":
            leads = CrmLead.sudo().search(
                [("email_from", "=", partner.email), ("stage_id.name", "=", "New")])
            if not leads:
                leads = False
            if leads == False:
                total_count = False

        elif filterby == "2":
            leads = CrmLead.sudo().search(
                [("email_from", "=", partner.email), ("stage_id.name", "=", ["Qualified","Proposition"])])

            if not leads:
                leads = False
            if leads == False:
                total_count = False
        elif filterby == "4":
            leads = CrmLead.sudo().search(
                [("email_from", "=", partner.email), ("stage_id.name", "=", "Won")])
            if not leads:
                leads = False
            if leads == False:
                total_count = False
        elif filterby == "5":
            leads = False
            if not leads:
                leads = False
            if leads == False:
                total_count = False
        else :
            leads = False
            if not leads:
                leads = False
            if leads == False:
                total_count = False
        values.update(
            {
                "date": date_begin,
                "total_count": total_count,
                "leads": leads,
                "page_name": "lead",
                "pager": pager,
                "default_url": "/my/leads",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "searchbar_filters": searchbar_filters,
                "filterby": filterby,
                "noFilter": noFilter,
                "new_lead_count": new_lead_count,
                "progress_lead_count": progress_lead_count,
                "done_lead_count": done_lead_count,
                "cancelled_lead_count": cancelled_lead_count,
                "title": "CRM | Dashboard",
                "dashboard_class": "active",
            }

        )
        return request.render("crmfront.crmfront_dashboard", values)

    @route("/new/lead", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        email = http.request.env.user.email        
        categories = http.request.env["crm.lead.category"].sudo().search([])
        services = http.request.env["product.template"].sudo().search([
            ('type','=','service'),
            ('company_id','=',1)
        ])
        name = http.request.env.user.name
        return http.request.render("crmfront.crm_dashboard_form",{
                "email": email,
                "name": name,
                'categories':categories,
                "services":services,
                "title": "CRM | New Lead",
                "ticket_class": "active",
            },
        )

    @route("/submitted/request", type="http", auth="user", website=True, csrf=True)
    def submit_ticket(self, **kw):
        email = http.request.env.user.email        
        customer = http.request.env['res.partner'].sudo().search(
                    [('email', '=', email),('customer', '=', True)], limit=1)
        
        values = {
            'stage_id': 1,
            'type': 'lead',
            'name': kw.get("subject"),
            'contact_name': kw.get("name"),
            'email_from': kw.get("email"),
            'partner_name': kw.get("name"),
            "category_id": int(kw.get("category")),
            "service_id": int(kw.get("service")),
            'phone': customer.phone,
            'country_id': customer.country_id.id,
            'city': customer.city,
            "partner_id": customer.id,
            'description': kw.get("description"),
            "company_id": 1,
        }

        new_lead = request.env['crm.lead'].sudo().create(values)
        new_lead.message_subscribe(
            partner_ids=request.env.user.partner_id.ids)
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "crm.lead",
                            "res_id": new_lead.id,
                        }
                    )
        
        return werkzeug.utils.redirect("/new/lead/submitted")
        
    @http.route("/new/lead/submitted", type="http", auth="user", website=True, csrf=False)
    def Lead_submitted(self, **kw):
        email = http.request.env.user.email        
        partner = http.request.env['res.partner'].sudo().search(
                    [('email', '=', email),('customer', '=', True)], limit=1)
        return http.request.render(
            "crmfront.crm_lead_submitted", {
            "title": "CEP | Lead Submitted",
            "ticket_class": "active"}
        )

    @http.route(["/my/lead/<int:lead_id>"], type="http", website=True)
    def portal_my_lead(self, lead_id=None, **kw):
        email = http.request.env.user.email        
        partner = http.request.env['res.partner'].sudo().search(
                    [('email', '=', email),('customer', '=', True)], limit=1)
        """if not partner:
            return request.render("crmfront.non_customer_template")"""
        lead = request.env["crm.lead"].sudo().search([("id", "=", lead_id)])
        comments = request.env["mail.message"].sudo().search(
            [("res_id", "=", lead.id), ("model", "=", "crm.lead"), ("message_type", "=", "comment")])
        total_comments = 0
        for comment in comments:
            total_comments += 1

        now = datetime.now()
        values = {
            'lead': lead,
            'ticket': False,
            'comments': comments,
            'total_comments': total_comments,
            "ticket_class": "active",
            'now': now,

        }

        return request.render("crmfront.portal_my_lead_page", values)

    @http.route("/new/comment", type="http", auth="user", website=True, csrf=True)
    def submit_comment(self, **kw):
        email = http.request.env.user.email
        partner = http.request.env['res.partner'].sudo().search(
                    [('email', '=', email),('customer', '=', True)], limit=1)

        if kw:
            lead = http.request.env['crm.lead'].sudo().search(
                [("id", "=", int(kw['lead_id']))], limit=1)
            any_message = http.request.env['mail.message'].sudo().search(
                [("res_id", "=", lead.id), ("model", "=", "crm.lead")], limit=1)

            http.request.env['mail.message'].sudo().create({
                'body': kw['comment'],
                'description': kw['comment'],
                'res_id': lead.id,
                'model': 'crm.lead',
                'message_type': 'comment',
                'display_name': lead.lead_number,
                'author_id': partner.id,

            })
            return werkzeug.utils.redirect("/my/lead/" + str(lead.id))
        else:
            return werkzeug.utils.redirect("/my/leads/")

    