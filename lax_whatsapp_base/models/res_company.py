# -*- coding: utf-8 -*-
# Part of LaxiconSolution. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
import urllib.request
from urllib.parse import quote
import requests
import json
import re


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_whatsapp_server = fields.Boolean(string="Use Whatsapp?")
    instance_id = fields.Char("Instance ID")
    whatsapp_access_token = fields.Char("Access Token")
    whatsapp_number = fields.Char('Whatsapp Number')
    whatsapp_url = fields.Char('URL', default="https://laxicon.co.in")

    def get_whatsapp_url(self):
        url = self.whatsapp_url or """https://laxicon.co.in"""
        url += "/api/send?"
        url += "instance_id=" + str(self.instance_id)
        url += "&access_token=" + str(self.whatsapp_access_token)
        return url

    def check_whatsapp_active(self):
        if not self.whatsapp_number:
            raise UserError("Please Add Testing Whatsapp Number")
        if self.whatsapp_number and self.whatsapp_access_token and self.instance_id and self.whatsapp_url:
            mobile_no = self.whatsapp_number
            mobile_no = mobile_no.split(",")
            for res in mobile_no:
                text_message = "testing for whatsapp"
                url = self.get_whatsapp_url()
                url += "&number=" + str(res.replace(" ", "").strip())
                url += "&type=text&message=" + text_message
                headers = {'Content-Type': 'application/json'}
                requests.post(url, headers=headers)

    def send_to_whatsapp(self, whatsapp_number, text_message, filename=None, media_url=None):
        url = self.get_whatsapp_url()
        for rec in self:
            whatsapp_number = whatsapp_number.replace(" ", "").strip() #.replace("+", "")
            whatsapp_number = re.sub(r'\D', '', whatsapp_number)
            encode_media_url = ''
            if media_url:
                url_parts = media_url.split("/")
                encoded_url = quote(url_parts[0], safe='')  # Encode scheme (http)
                encoded_url += "/" + "/".join(quote(part, safe='') for part in url_parts[1:])
                encode_media_url = encoded_url
            url += "&number=" + str(whatsapp_number)
            url += "&message=" + text_message
            if not media_url:
                url += "&type=text"
            if media_url:
                url += "&type=media"
                url += "&media_url=" + encode_media_url
                url += "&filename=" + filename
            headers = {
                  'Content-Type': 'application/json'
                }
            res = requests.post(url, headers=headers)
            if res.status_code == 200:
                response_data = json.loads(res.text)
                if isinstance(response_data, dict) and response_data.get('status') == 'success':
                    return True
            return False


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    use_whatsapp_server = fields.Boolean(related="company_id.use_whatsapp_server",readonly=False)
    instance_id = fields.Char(related="company_id.instance_id",readonly=False)
    whatsapp_access_token = fields.Char(related="company_id.whatsapp_access_token",readonly=False)
    whatsapp_number = fields.Char(related="company_id.whatsapp_number",readonly=False)
    whatsapp_url = fields.Char(related="company_id.whatsapp_url",readonly=False)


    def check_whatsapp_active(self):
        self.env.user.company_id.check_whatsapp_active()
