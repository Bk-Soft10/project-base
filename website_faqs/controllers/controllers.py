# -*- coding: utf-8 -*-
from odoo import http
import re


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


class WebsiteFaqs(http.Controller):
    @http.route(['/faqs'], auth='public', website=True, type='http')
    def faq(self, **kw):
        if http.request.website.show_faq:
            category = int(kw.get('cat', 0))
            if category == 0:
                faq_ids = http.request.env['website.faq.faqs'].search(
                    [('state', '=', 'published'), ('website_id', '=', http.request.website.id)])
            else:
                faq_ids = http.request.env['website.faq.faqs'].search(
                    [('state', '=', 'published'), ('category', '=', category),
                     ('website_id', '=', http.request.website.id)])

            faq = {}
            if not faq_ids:
                return http.request.render("website_faqs.empty_page")

            for faq_id in faq_ids:
                category = faq_id.category.name
                tag = faq_id.main_tag.name
                if category not in faq:
                    faq[category] = [{tag: []}]
                else:
                    for tag_dict in faq[category]:
                        if tag not in tag_dict:
                            tag_dict[tag] = []

            for faq_id in faq_ids:
                category = faq_id.category.name
                tag = faq_id.main_tag.name
                question = faq_id.name
                id_faq = faq_id.id

                if category in faq:
                    for tag_dict in faq[category]:
                        if tag in tag_dict:
                            tag_dict[tag].append({'question': question, 'faq_id': id_faq})

            categories = []
            all_faq_ids = http.request.env['website.faq.faqs'].search(
                [('state', '=', 'published'), ('website_id', '=', http.request.website.id)])
            for cat in all_faq_ids:
                category_id = cat.category.id
                categories.append(category_id)

            cat_ids = set(categories)
            cat_ids = http.request.env['website.faq.category'].search([('id', 'in', list(cat_ids))])
            categories = []
            for cat in cat_ids:
                categories.append({'cat_id': cat.id, 'cat_name': cat.name})

            highlight = ''
            if len(faq) > 1:
                highlight = 'all'
            elif len(faq) == 1:
                for key in faq:
                    highlight = key
            values = {
                'data': faq,
                'category': categories,
                'highlight': highlight,
            }
            return http.request.render("website_faqs.all_faqs", values)
        else:
            return http.request.render('http_routing.404')

    @http.route(['/faq/autocomplete'], auth='public', website=True, type='json')
    def faq_auto(self, term, max_nb_chars=999, **kw):
        if http.request.website.show_faq:
            matches_ids = http.request.env['website.faq.faqs'].search(
                ['&', '|', ('name', 'ilike', term), ('main_tag', 'ilike', term), '&', ('state', '=', 'published'),
                 ('website_id', '=', http.request.website.id)])
            values = []
            for faq in matches_ids:
                text = clean_html(faq.answer)
                if len(text) > max_nb_chars:
                    ans = text[:max_nb_chars - 3] + "..."
                else:
                    ans = text
                values.append(
                    {'faq_id': faq.id, 'faq_tag': faq.main_tag.name, 'faq_question': faq.name, 'faq_ans': ans})

            return {'faqs': values}
        else:
            return http.request.render('http_routing.404')

    @http.route(['/faq'], auth='public', website=True, type='http')
    def question(self, **kw):
        if http.request.website.show_faq:
            faq_id = int(kw.get('faq', 0))
            values = {}

            if faq_id > 0:
                faq_obj = http.request.env['website.faq.faqs'].search(
                    [('id', '=', faq_id), ('state', '=', 'published'), ('website_id', '=', http.request.website.id)])
                if not faq_obj:
                    return http.request.render("website_faqs.error_page")
                feedback = int(kw.get('fb', -1))
                if feedback != -1:
                    if feedback == 1:
                        faq_obj.ups = faq_obj.ups + 1
                    if feedback == 0:
                        faq_obj.downs = faq_obj.downs + 1
                    values['feedback'] = True

                values['faq_id'] = faq_obj.id
                values['tag'] = faq_obj.main_tag.name
                values['question'] = faq_obj.name
                values['ans'] = faq_obj.answer
                return http.request.render("website_faqs.spec_faq", values)
            else:
                return http.request.render("website_faqs.error_page")
        else:
            return http.request.render('http_routing.404')
