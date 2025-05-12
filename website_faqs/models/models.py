# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FaqCategory(models.Model):
    _name = "website.faq.category"

    name = fields.Char('Name')


class FaqMainTag(models.Model):
    _name = "website.faq.main.tag"

    name = fields.Char()


class WebsiteFaqs(models.Model):
    _name = "website.faq.faqs"

    name = fields.Char('Question')
    category = fields.Many2one('website.faq.category', string='FAQ Category')
    main_tag = fields.Many2one('website.faq.main.tag', string='Tag')
    website_id = fields.Many2one('website', string='Show on')
    state = fields.Selection([('unpublished', 'Unpublished'), ('published', 'Published')], default='unpublished')
    answer = fields.Html(sanitize=False)
    ups = fields.Integer('Likes')
    downs = fields.Integer('Dislikes')

    def publish_faq(self):
        self.state = 'published'

    def un_publish_faq(self):
        self.state = 'unpublished'

    def likes(self):
        pass

    def dislikes(self):
        pass


class FaqSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_faq = fields.Boolean(related='website_id.show_faq', readonly=False, string='Show FAQ Menu')


class Website(models.Model):
    _inherit = "website"

    show_faq = fields.Boolean('Show FAQ Menu')
