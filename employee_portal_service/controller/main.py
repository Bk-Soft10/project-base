# -*- encoding: utf-8 -*-

import os
import base64
import json
import werkzeug
import werkzeug.utils
import odoo.modules.registry
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError
from odoo import http, fields, _, SUPERUSER_ID
from odoo.http import request
from odoo.tools import consteq, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools.safe_eval import safe_eval
from operator import itemgetter
from psycopg2 import IntegrityError
import logging

_logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = {
    'code': 100,
    'message': 'Invalid Credentials',
}
DATA_NOT_FOUND = {
    'code': 101,
    'message': 'Data not available',
}
INVALID_REQUEST = {
    'code': 102,
    'message': 'Invalid Request',
}


def response_ok(result):
    response = {
        'code': 200,
        'result': result,
    }
    return json.dumps(response)


def response_nodata():
    return json.dumps(DATA_NOT_FOUND)


def response_invalidcredentials():
    return json.dumps(INVALID_CREDENTIALS)


def response_invalidrequest():
    return json.dumps(INVALID_REQUEST)


try:
    import base64
except ImportError:
    base64 = None

PPG = 10  # Per Page
PPR = 4  # Per Row


def get_records_pager(ids, current):
    if current.id in ids and (hasattr(current, 'website_url') or hasattr(current, 'access_url')):
        attr_name = 'access_url' if hasattr(current, 'access_url') else 'website_url'
        idx = ids.index(current.id)
        return {
            'prev_record': idx != 0 and getattr(current.browse(ids[idx - 1]), attr_name),
            'next_record': idx < len(ids) - 1 and getattr(current.browse(ids[idx + 1]), attr_name),
        }
    return {}


class EmployeePortal(http.Controller):
    _items_per_page = 20

    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.with_user(SUPERUSER_ID).exists()
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        try:
            document.check_access_rights('read')
            document.check_access_rule('read')
        except AccessError:
            if not access_token or not document_sudo.access_token or not consteq(document_sudo.access_token, access_token):
                raise
        return document_sudo

    def _get_page_view_values(self, document, access_token, values, session_history, no_breadcrumbs, **kwargs):
        if access_token:
            # if no_breadcrumbs = False -> force breadcrumbs even if access_token to `invite` users to register if they click on it
            values['no_breadcrumbs'] = no_breadcrumbs
            values['access_token'] = access_token
            values['token'] = access_token  # for portal chatter

        # Those are used notably whenever the payment form is implied in the portal.
        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']
        # Email token for posting messages in portal view with identified author
        if kwargs.get('pid'):
            values['pid'] = kwargs['pid']
        if kwargs.get('hash'):
            values['hash'] = kwargs['hash']

        history = request.session.get(session_history, [])
        values.update(get_records_pager(history, document))

        return values

    def get_home_page_contents(self):
        """@return: array of dict for homepage's content."""
        page_content = {}
        smart_button = {'req_follow': 0, 'req_validate': 0}
        user = request.env.user
        emp_obj = request.env['hr.employee']
        employee_id = emp_obj.sudo().search([('user_id', '=', user.id)], limit=1)
        transactions_content = self.get_transactions_page_contents('all')
        follow_transactions = transactions_content['follow_transactions']
        validate_transactions = transactions_content['waiting_actions']
        smart_button['req_follow'] = len(follow_transactions)
        smart_button['req_validate'] = len(validate_transactions)
        page_content['smart_button'] = smart_button
        page_content['user'] = user
        page_content['employee'] = employee_id
        page_content['follow_transactions'] = follow_transactions[:7]
        page_content['validate_transactions'] = validate_transactions[:7]
        return page_content

    ##################################################################################################################
    #################################################################################################################

    @http.route('/portal/home', auth="user", website=True)
    def employee_portal_home(self, **kw):
        page_context = self.get_home_page_contents()
        return request.render("employee_portal_service.portal_home", page_context)

    ##################################################################################################################
    #################################################################################################################

    def init_action_filters(self, action_filters):
        for rec in action_filters:
            rec['active'] = False
        return action_filters

    def get_button_actions(self, record_id, model):
        user = request.env.user
        obj = request.env[model].sudo().browse([int(record_id)])
        transaction_obj = request.env['portal.transaction.setting'].sudo()
        applied_settings = transaction_obj.search([
            ('group_id', 'in', user.groups_id.ids or []), ('model_id.model', '=', model),
            ('transaction_type', '=', 'validate')])
        res = {}
        for setting in applied_settings:
            final_records = request.env[setting.model_id.model].sudo().search(
                safe_eval(setting.domain.replace('request.uid', str(request.uid)) or '[]')
            )
            # apply filter
            after_searching_filter = safe_eval(setting.after_searching_filter or '{}')
            filtered_records = []
            if after_searching_filter:
                for itemkey, itemval in after_searching_filter.items():
                    filtered_records += final_records.filtered(lambda record: getattr(record, itemkey) == itemval)
                final_records = filtered_records
            if obj in final_records:
                res = {'object': obj,
                       'confirm_action': setting.transaction_approve_method,
                       'refuse_action': setting.transaction_refuse_method,
                       'field_refuse_reason': setting.field_refuse_reason}
                break
        return res

    def get_transaction_name(self, name, transaction_type, rec):
        return name

    def get_transactions(self, filter_name='all', transaction_types=['validate', 'follow']):
        """Get transactions."""
        user = request.env.user
        applied_settings = request.env['portal.transaction.setting'].sudo().search([
            ('group_id', 'in', user.groups_id.ids or []), ('transaction_type', 'in', transaction_types)
        ])
        result_lines = []
        for setting in applied_settings:
            final_records = request.env[setting.model_id.model].sudo().search(
                safe_eval(setting.domain.replace('request.uid', str(request.uid)) or '[]')
            )
            # apply filter
            after_searching_filter = safe_eval(setting.after_searching_filter or '{}')
            filtered_records = []
            if after_searching_filter:
                for itemkey, itemval in after_searching_filter.items():
                    filtered_records += final_records.filtered(lambda record: getattr(record, itemkey) == itemval)
                final_records = filtered_records
            result_line = {'setting': setting, 'records': list(set(final_records))}
            result_lines.append(result_line)
        # data and filters
        res = []
        actions_filters = []
        for line in result_lines:
            for rec in line.get('records', []):
                item = dict()
                setting = line.get('setting')
                name = self.get_transaction_name(setting.transaction_label, setting.transaction_type, rec)
                obj_fields = rec.fields_get()
                details_url = False
                if setting.details_url:
                    details_url = setting.details_url + str(rec.id)
                sel_value = ''
                state_col = False
                if obj_fields and 'state' in obj_fields:
                    state_col = rec.state
                    sel_value = [item[1] for item in obj_fields['state']['selection'] if item[0] == rec.state]
                    if sel_value:
                        sel_value = sel_value[0]
                    else:
                        sel_value = ''
                item.update(name=name,
                            code=setting.transaction_label,
                            display_button_accept=setting.display_button_accept,
                            display_button_refuse=setting.display_button_refuse,
                            display_button_details=setting.display_button_details,
                            transaction_type=setting.transaction_type,
                            record_id=rec.id,
                            state=state_col,
                            state_value=sel_value or False,
                            model=rec._name,
                            fields=str(line.get('fields', '')),
                            details_url=details_url,
                            number=getattr(rec, setting.transaction_field_number.name),
                            ddate=getattr(rec, setting.transaction_field_date.name))
                res.append(item)
            actions_filters.append({
                'code': line['setting'].transaction_label,
                'transaction_type': line['setting'].transaction_type,
                'name': line['setting'].transaction_label,
                'count': len(line.get('records', [])),
                'active': False
            })
        for dict_fil in actions_filters:
            if dict_fil['code'] == filter_name and dict_fil['transaction_type'] in transaction_types:
                dict_fil['active'] = True
                res = list(filter(lambda d: d['code'] == filter_name, res))
        # sort by date
        # res = sorted(res, key=itemgetter('ddate'), reverse=True)
        return res, actions_filters

    def get_transactions_page_contents(self, filter_name='all'):
        """@return: array of dict for homepage's content."""
        transactions_content = {}
        smart_buttons = {'new_actions': 0, 'pending_actions': 0, 'all_actions': 0}
        # fill transactions_content
        transactions_content['follow_transactions'] = self.get_transactions(filter_name, ['follow'])[0]
        transactions_content['validate_transactions'] = self.get_transactions(filter_name, ['validate'])[0]
        transactions_content['smart_buttons'] = smart_buttons
        return transactions_content

    @http.route(['/portal/transactions'], type='http', auth="user", website=True)
    def list_waiting_transactions(self, filter_name='all', transaction_type='follow'):
        """List of waiting transaction."""
        actions, actions_filters = self.get_transactions(filter_name, [transaction_type])
        # smart buttons
        smart_buttons = {'new_actions': 0, 'pending_actions': 0, 'all_actions': len(actions)}
        for action in actions:
            if action['state'] in ['new', 'draft']:
                smart_buttons['new_actions'] += 1
            elif action['state'] not in ['new', 'draft', 'finish', 'done', 'finished']:
                smart_buttons['pending_actions'] += 1
        return request.render('app_website_base.waiting_transactions_list_page', qcontext={
            'actions': actions,
            'smart_buttons': smart_buttons,
            'transaction_type': transaction_type,
            'has_employee': True,
            'actions_filters': actions_filters
        })

    @http.route('/portal/transaction/refuse', type='json', methods=['POST'], auth="user", website=True)
    def refuse_transaction(self, **arg):
        """Refuse transaction."""
        record_id = arg.get('record_id', False)
        model = arg.get('model', False)
        buttons = self.get_button_actions(record_id, model)
        reason_msg = arg.get('reason_msg', False)
        if not reason_msg:
            return json.dumps([{'error': 'Please Insert Reject Reason'}])
        try:
            # create a refuse wizard
            wiz = request.env['hr.refuse.wizard'].with_context({
                'active_id': int(record_id),
                'active_model': model,
                'field_name': buttons['field_refuse_reason'],
                'action_name': buttons['refuse_action']
            }).sudo().create({'message': reason_msg})

            if wiz:
                wiz.button_refuse()
                return json.dumps([{'success': 'Reject Successfully'}])
            else:
                return json.dumps([{'error': 'The Mission Failed'}])

        except ValidationError as msg:
            error = str(msg.name)
            http.request._cr.rollback()
            return json.dumps([{'error': error}])
        except IntegrityError as msg:
            http.request._cr.rollback()
            error = str(msg.args[0])
            return json.dumps([{'error': error}])

    @http.route('/portal/json/accept-transactions', type='json', methods=['POST'], auth="user", website=True)
    def accept_transactions(self, **kw):
        """Accept transaction."""
        values = request.params.copy()
        try:
            record_id = values.get('record_id', False)
            model = values.get('model', False)
            buttons = self.get_button_actions(record_id, model)
            if buttons:
                getattr(buttons['object'], buttons['confirm_action'], False)()
            return json.dumps([{'success': 'ok'}])
        except Exception:
            http.request._cr.rollback()
            error = 'Error >> Proccess'
            return json.dumps([{'error': error}])

    @http.route('/portal/transactions/process', type='json', auth="user", website=True)
    def details_transactions(self, **arg):
        """Accept transaction."""
        action = arg.get('action', False)
        record_id = arg.get('record_id', False)
        model = arg.get('model', False)
        buttons = self.get_button_actions(record_id, model)
        try:
            if action and buttons:
                if action == 'confirm':
                    getattr(buttons['object'], buttons['confirm_action'], False)()
                    return json.dumps([{'success': 'Success'}])
        except ValidationError as msg:
            error = str(msg.name)
            http.request._cr.rollback()
            return json.dumps([{'error': error}])
