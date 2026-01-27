import json
import copy
import datetime
import logging

import requests
import time
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


def _sanitize_null_bytes(value):
    """Remove NULL bytes that PostgreSQL cannot store in JSON/text fields.

    PostgreSQL's jsonb type cannot handle \u0000 (NULL byte) characters.
    These often appear in content copied from PDFs or due to encoding issues.
    """
    if isinstance(value, str):
        return value.replace('\x00', '').replace('\u0000', '')
    elif isinstance(value, dict):
        return {k: _sanitize_null_bytes(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_null_bytes(v) for v in value]
    return value


def _is_valid_translatable_value(value):
    """Check if a value is valid for translation.

    Returns False for: None, False (bool), empty strings, whitespace-only strings.
    Returns True for non-empty strings (including HTML content).
    """
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return False


class TranslationAction(models.Model):
    _name = 'otk.translation.action'
    _description = 'Translation Action'
    _rec_name = 'display_name'
    _order = 'id desc'

    display_name = fields.Char(string="Name", compute='_compute_display_name', store=True, readonly=True)

    model_id = fields.Many2one('ir.model', string="Model", ondelete='cascade', readonly=True)
    base_language_id = fields.Many2one('res.lang', string="Language", readonly=True)
    target_language_ids = fields.Many2many('res.lang', string="Target languages", required=True, ondelete='cascade',
                                           readonly=True)
    field_ids = fields.Many2many(
        'ir.model.fields',
        string="Fields to translate",
        domain="[('translate', '=', True), ('model_id', '=', model_id)]",
        readonly=True,
    )
    pending_record_ids = fields.Json(default=list, string="Pending translations", readonly=True)
    processing_record_ids = fields.Json(default=list, string="Processing translations", readonly=True)
    done_record_ids = fields.Json(default=list, string="Done translations", readonly=True)
    error_record_ids = fields.Json(default=list, string="Error translations", readonly=True)
    progress = fields.Float(store=True, string="Progress", compute="_compute_progress", readonly=True)
    translation_count = fields.Integer(readonly=True, string="Translation count")
    token_cost = fields.Integer(default=0, string="Token used", readonly=True)

    translation_ids = fields.One2many(
        comodel_name='otk.translation',
        inverse_name='action_id',
        string='Translations',
        readonly=True)

    status = fields.Selection(
        [('pending', 'Pending'), ('done', 'Done'), ('error', 'Error'), ('processing', 'Processing')],
        compute='_compute_status',
        string='Status',
        store=True
    )

    def _get_error_message_for_status(self, status_code, response_text=""):
        """Get a user-friendly error message based on HTTP status code."""
        error_messages = {
            400: _("Invalid request data"),
            401: _("Your API key is invalid. Use a valid key and restart the translation from the parent action."),
            403: _("Access denied to the translation service"),
            404: _("Translation service endpoint not found"),
            429: _("Too many requests. The service is rate-limited."),
            500: _("Translation service internal error"),
            502: _("Translation service temporarily unavailable (bad gateway)"),
            503: _("Translation service is currently unavailable"),
            504: _("Translation service request timed out"),
        }
        return error_messages.get(status_code, _("An error has occurred (HTTP %d). You can restart the translation from the parent action.") % status_code)

    def _create_error_translation(self, record_id, status_code, error_details=""):
        """Create a translation record with error status and detailed message."""
        if status_code == 401:
            status = 'api_key_error'
        else:
            status = 'translation_error'

        error_message = self._get_error_message_for_status(status_code)
        if error_details:
            error_message = f"{error_message}\nDetails: {error_details}"

        self.env["otk.translation"].create({
            'action_id': self.id,
            'cost': 0,
            'record_id': record_id,
            'status': status,
            'translations': error_message,
        })

    def _move_record_to_error(self, record_id):
        """Move a record from pending to error state."""
        pending = self.pending_record_ids if self.pending_record_ids else []
        error = self.error_record_ids if self.error_record_ids else []
        if record_id in pending:
            pending.remove(record_id)
        if record_id not in error:
            error.append(record_id)
        self.write({
            'pending_record_ids': pending,
            'error_record_ids': error,
        })

    def _mark_pending_translations_as_error(self, translations, error_message):
        """Mark multiple pending translations as error with a message."""
        for translation in translations:
            translation.write({
                'status': 'translation_error',
                'translations': error_message,
            })
            # Move record to error state in the action
            action = translation.action_id
            if action:
                processing = action.processing_record_ids if action.processing_record_ids else []
                error_ids = action.error_record_ids if action.error_record_ids else []
                record_id = translation.record_id
                if record_id in processing:
                    try:
                        processing.remove(record_id)
                    except ValueError:
                        pass
                if record_id not in error_ids:
                    error_ids.append(record_id)
                action.write({
                    'processing_record_ids': processing,
                    'error_record_ids': error_ids,
                })

    def translate_model(self, model, target_langs, record_id):
        api_key = self.env['ir.config_parameter'].sudo().get_param('otoolkit_api_key')
        api_endpoint = self.env['ir.config_parameter'].sudo().get_param('otoolkit.api.endpoint')

        if not api_key:
            _logger.error("OToolKit API key not configured for bulk translation")
            self._create_error_translation(record_id, 401, "API key not configured")
            self._move_record_to_error(record_id)
            return False

        if not api_endpoint:
            _logger.error("OToolKit API endpoint not configured for bulk translation")
            self._create_error_translation(record_id, 500, "API endpoint not configured")
            self._move_record_to_error(record_id)
            return False

        payload = json.dumps({
            "object": model,
            "target_langs": target_langs,
            "record_id": record_id,
            "odoo_user_id": self.env.user.id
        })

        headers = {
            'Odoo-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        url = f"{api_endpoint}/api/auto-translate-fields/v2/translate-model/"

        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout=180)
        except requests.exceptions.Timeout:
            _logger.warning("OToolKit API request timed out for record %d: %s", record_id, url)
            self._create_error_translation(record_id, 504, "Request timed out")
            self._move_record_to_error(record_id)
            return False
        except requests.exceptions.ConnectionError as e:
            _logger.error("OToolKit API connection error for record %d: %s - %s", record_id, url, str(e))
            self._create_error_translation(record_id, 503, f"Connection error: {str(e)}")
            self._move_record_to_error(record_id)
            return False
        except requests.exceptions.RequestException as e:
            _logger.error("OToolKit API request failed for record %d: %s - %s", record_id, url, str(e))
            self._create_error_translation(record_id, 500, f"Request failed: {str(e)}")
            self._move_record_to_error(record_id)
            return False

        if response.status_code != 200:
            # Try to extract error details from response
            error_details = ""
            try:
                error_json = response.json()
                error_details = error_json.get("error", "") or error_json.get("detail", "")
                error_type = error_json.get("type", "")
                if error_type:
                    error_details = f"[{error_type}] {error_details}"
            except (json.JSONDecodeError, KeyError):
                error_details = response.text[:200] if response.text else ""

            _logger.warning(
                "OToolKit API returned status %d for record %d: %s",
                response.status_code, record_id, error_details
            )

            self._create_error_translation(record_id, response.status_code, error_details)
            self._move_record_to_error(record_id)
            return False

        try:
            data = response.json()
            return data["task_id"]
        except (json.JSONDecodeError, KeyError) as e:
            _logger.error("Failed to parse OToolKit API response for record %d: %s", record_id, str(e))
            self._create_error_translation(record_id, 500, f"Invalid response format: {str(e)}")
            self._move_record_to_error(record_id)
            return False

    def cron_translate_action(self):
        max_time = 60
        max_record = 10
        max_iter = 10
        action = self.env['otk.translation.action'].sudo().search([('status', '=', 'pending')], order='id asc', limit=1)
        start = int(time.time())

        while action and max_iter > 0:
            can_restart = self.translate_action(action, max_record)
            if not can_restart:
                break
            action = self.env['otk.translation.action'].sudo().search([('status', '=', 'pending')], order='id asc',
                                                                      limit=1)
            if int(time.time()) - start > max_time:
                break

            max_iter -= 1

        self.cron_retrieve_tasks()

    def cron_retrieve_tasks(self):
        pending_translations = self.env["otk.translation"].sudo().search(
            [('status', '=', 'pending')], order='id asc', limit=100
        )

        if len(pending_translations) == 0:
            return

        api_key = self.env['ir.config_parameter'].sudo().get_param('otoolkit_api_key')
        api_endpoint = self.env['ir.config_parameter'].sudo().get_param('otoolkit.api.endpoint')
        if not api_key:
            return

        payload = json.dumps({
            "task_ids": pending_translations.mapped('task_id'),
        })

        headers = {
            'Odoo-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        url = f"{api_endpoint}/api/tasks/"

        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout=120)
        except requests.exceptions.Timeout:
            _logger.error("OToolKit API timeout while retrieving tasks")
            self._mark_pending_translations_as_error(pending_translations, "API timeout while retrieving translation status")
            return
        except requests.exceptions.ConnectionError as e:
            _logger.error("OToolKit API connection error while retrieving tasks: %s", str(e))
            self._mark_pending_translations_as_error(pending_translations, f"Connection error: {str(e)}")
            return
        except requests.exceptions.RequestException as e:
            _logger.error("OToolKit API request failed while retrieving tasks: %s", str(e))
            self._mark_pending_translations_as_error(pending_translations, f"Request failed: {str(e)}")
            return

        if response.status_code != 200:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_json = response.json()
                error_detail = error_json.get("error", "") or error_json.get("detail", "")
                if error_detail:
                    error_msg = f"{error_msg}: {error_detail}"
            except (json.JSONDecodeError, KeyError):
                if response.text:
                    error_msg = f"{error_msg}: {response.text[:200]}"
            _logger.error("OToolKit API error while retrieving tasks: %s", error_msg)
            self._mark_pending_translations_as_error(pending_translations, error_msg)
            return

        try:
            tasks = response.json()["tasks"]
        except (json.JSONDecodeError, KeyError) as e:
            _logger.error("Failed to parse OToolKit API response for tasks: %s", str(e))
            self._mark_pending_translations_as_error(pending_translations, f"Invalid API response format: {str(e)}")
            return

        task_map = {task["id"]: task for task in tasks}
        action_update = {}

        for translation in pending_translations:
            action_id = translation.action_id.id
            if action_id not in action_update:
                action_update[action_id] = {
                    'error': [],
                    'completed': [],
                    'action': translation.action_id,
                }

            related_task = task_map.get(translation.task_id)

            # Skip if task not found in API response (still pending on server side)
            if not related_task:
                continue

            # Safely extract record_id with error handling
            try:
                active_id = related_task['params']['record_id']
            except (KeyError, TypeError) as e:
                _logger.error("Invalid task structure for task %s: missing params.record_id - %s", translation.task_id, str(e))
                translation.write({
                    'status': 'translation_error',
                    'translations': f"Invalid task response structure: {str(e)}",
                })
                action_update[action_id]['error'].append(translation.record_id)
                continue

            if related_task["status"] == "completed":
                try:
                    action_update[action_id]['completed'].append(active_id)
                    action = action_update[action_id]['action']
                    record = self.env[action.model_id.model].with_context(lang=action.base_language_id.code).browse(active_id)

                    translatable_object = related_task['params']['object']
                    target_langs = related_task['params']['target_langs']
                    translations = related_task['result']['translated_object']
                    cost = related_task['result'].get('cost', 0)

                    previous_values = {}

                    for field in action.field_ids:
                        if not hasattr(record, field.name):
                            continue

                        base_value = translatable_object.get(field.name)
                        if base_value:
                            translate_column = f"{field.name}"

                            query = f"""
                                                    SELECT {translate_column}
                                                    FROM {self.env[action.model_id.model]._table}
                                                    WHERE id = %s
                                                """
                            self.env.cr.execute(query, (active_id,))
                            result = self.env.cr.fetchone()
                            # Sanitize existing translations from DB in case they contain NULL bytes
                            translate = _sanitize_null_bytes(result[0]) if result and result[0] else {}

                            # Sanitize base_value to remove NULL bytes
                            translate[action.base_language_id.code] = _sanitize_null_bytes(base_value)
                            previous_values[field.name] = copy.deepcopy(translate)

                            for lang in target_langs:
                                # Safely access nested translation with validation
                                field_translations = translations.get(field.name, {})
                                if isinstance(field_translations, dict) and lang in field_translations:
                                    # Sanitize the translated value from API
                                    translate[lang] = _sanitize_null_bytes(field_translations[lang])
                                else:
                                    _logger.warning("Missing translation for field %s, lang %s in record %d", field.name, lang, active_id)

                            # Sanitize the entire translate dict to remove NULL bytes
                            # that PostgreSQL cannot store in jsonb fields
                            sanitized_translate = _sanitize_null_bytes(translate)

                            update_query = f"""
                                                            UPDATE {self.env[action.model_id.model]._table}
                                                            SET {translate_column} = %s
                                                            WHERE id = %s
                                                        """
                            self.env.cr.execute(update_query, (json.dumps(sanitized_translate), active_id))

                    translation.write({
                        'cost': cost,
                        'status': 'success',
                        'translations': translations,
                        'initial_values': previous_values,
                    })
                    # Update last_translation_date only if the field exists on the model
                    # (for backward compatibility with models using the mixin)
                    if 'last_translation_date' in self.env[action.model_id.model]._fields:
                        record.write({
                            "last_translation_date": datetime.datetime.now(),
                        })
                except (KeyError, TypeError) as e:
                    _logger.error("Error processing completed task %s for record %d: %s", translation.task_id, active_id, str(e))
                    translation.write({
                        'status': 'translation_error',
                        'translations': f"Error processing translation result: {str(e)}",
                    })
                    # Move from completed to error
                    if active_id in action_update[action_id]['completed']:
                        action_update[action_id]['completed'].remove(active_id)
                    action_update[action_id]['error'].append(active_id)
                except Exception as e:
                    _logger.error("Unexpected error processing task %s for record %d: %s", translation.task_id, active_id, str(e))
                    translation.write({
                        'status': 'translation_error',
                        'translations': f"Unexpected error: {str(e)}",
                    })
                    if active_id in action_update[action_id]['completed']:
                        action_update[action_id]['completed'].remove(active_id)
                    action_update[action_id]['error'].append(active_id)

            elif related_task["status"] == "failed":
                # Extract error message from the API response
                error_message = "Translation failed"
                try:
                    result = related_task.get('result', {})
                    if isinstance(result, dict):
                        error_message = result.get('error', '') or result.get('message', '') or result.get('detail', '')
                    if not error_message:
                        error_message = str(result) if result else "Translation failed (no details provided)"
                except Exception:
                    error_message = "Translation failed (could not parse error details)"

                _logger.warning("Translation task %s failed for record %d: %s", translation.task_id, active_id, error_message)
                action_update[action_id]['error'].append(active_id)
                translation.write({
                    'status': 'translation_error',
                    'translations': error_message,
                })

        for key, value in action_update.items():
            action = value['action']
            processing = action.processing_record_ids if action.processing_record_ids else []
            error = action.error_record_ids if action.error_record_ids else []
            done = action.done_record_ids if action.done_record_ids else []

            for translation_id in value['completed']:
                try:
                    processing.remove(translation_id)
                except ValueError:
                    _logger.debug("Record %d not found in processing list", translation_id)
                if translation_id not in done:
                    done.append(translation_id)

            for translation_id in value['error']:
                try:
                    processing.remove(translation_id)
                except ValueError:
                    _logger.debug("Record %d not found in processing list", translation_id)
                if translation_id not in error:
                    error.append(translation_id)

            action.write({
                'processing_record_ids': processing,
                'error_record_ids': error,
                'done_record_ids': done,
            })

    def translate_action(self, action, max_record):
        active_ids = action.pending_record_ids[0:max_record]
        langs = action.target_language_ids
        target_langs = []
        for lang in langs:
            if lang.code != action.base_language_id.code:
                target_langs.append(lang.code)

        error_count = 0
        translations_to_create = []

        for active_id in active_ids:
            record = self.env[action.model_id.model].with_context(lang=action.base_language_id.code).browse(active_id)

            translatable_object = {}
            for field in action.field_ids:
                value = getattr(record, field.name)
                if _is_valid_translatable_value(value):
                    # Sanitize the value to remove NULL bytes before sending to API
                    translatable_object[field.name] = _sanitize_null_bytes(value)

            # Skip records with no translatable content
            if not translatable_object:
                _logger.warning("Skipping record %d: no valid translatable content found", active_id)
                action._create_error_translation(active_id, 400, "No valid translatable content found in selected fields")
                action._move_record_to_error(active_id)
                error_count += 1
                continue

            task_id = action.translate_model(translatable_object, target_langs, active_id)

            if not task_id:
                error_count += 1
                continue

            translations_to_create.append({
                'action_id': action.id,
                'cost': 0,
                'record_id': active_id,
                'status': 'pending',
                'translations': {},
                'initial_values': {},
                'task_id': task_id
            })

            pending = action.pending_record_ids if action.pending_record_ids else []
            processing = action.processing_record_ids if action.processing_record_ids else []
            pending.remove(active_id)
            if active_id not in processing:
                processing.append(active_id)
            action.write({
                'pending_record_ids': pending,
                'processing_record_ids': processing,
            })

        if translations_to_create:
            self.env["otk.translation"].create(translations_to_create)

        return error_count != len(active_ids)

    def retry_error_translation(self):
        for record in self:
            pending = record.pending_record_ids if record.pending_record_ids else []
            error = record.error_record_ids if record.error_record_ids else []
            pending.extend(error)
            self.write({
                'pending_record_ids': pending,
                'error_record_ids': [],
            })

    @api.depends('pending_record_ids', 'done_record_ids')
    def _compute_progress(self):
        for record in self:
            if not record.done_record_ids:
                record.progress = 0.0
            elif not record.pending_record_ids and not record.processing_record_ids:
                record.progress = 100.0
            else:
                record.progress = len(record.done_record_ids) / record.translation_count * 100.0

    @api.depends('progress', 'error_record_ids')
    def _compute_status(self):
        for record in self:
            if record.error_record_ids and len(record.error_record_ids) > 0 and (
                    not record.pending_record_ids or len(record.pending_record_ids) == 0) and (
                    not record.processing_record_ids or len(record.processing_record_ids) == 0):
                record.status = 'error'
            else:
                record.status = 'done' if record.progress >= 100 else 'pending' if record.pending_record_ids and len(
                    record.pending_record_ids) > 0 else 'processing'

    @api.depends('model_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = "Action #" + str(record.id) + " - " + record.model_id.name


class Translation(models.Model):
    _name = 'otk.translation'
    _description = 'Translation object with the details of the translation, the cost...'
    _order = 'id desc'

    action_id = fields.Many2one('otk.translation.action', string="Linked action", ondelete='cascade', readonly=True)
    record_id = fields.Integer(string='Record id', readonly=True)
    model_id = fields.Many2one('ir.model', string='Model', readonly=True, related='action_id.model_id')

    cost = fields.Float(string="Token used", readonly=True)
    status = fields.Selection(
        [
            ('error', "Error"),
            ('translation_error', "Translation Error"),
            ('api_key_error', "Api Key Error"),
            ('success', "Success"),
            ('revert', "Revert"),
            ('pending', "Pending"),
        ],
        string="Status", readonly=True
    )
    translations = fields.Json(string='Translations', readonly=True)
    initial_values = fields.Json(string='Initial value', readonly=True)

    task_id = fields.Integer(string="Task ID", readonly=True)

    def revert_translation(self):
        for record in self:
            initial = record.initial_values
            for field in record.translations:
                query = f"""
                            SELECT {field} 
                            FROM {self.env[record.model_id.model]._table} 
                            WHERE id = %s
                        """
                self.env.cr.execute(query, (record.record_id,))
                result = self.env.cr.fetchone()
                # Sanitize existing translations from DB in case they contain NULL bytes
                translate = _sanitize_null_bytes(result[0]) if result and result[0] else {}

                for lang in record.translations[field]:
                    initial_value = initial[field].get(lang)
                    if not initial_value:
                        initial_value = False
                    translate[lang] = initial_value

                # Sanitize to remove NULL bytes before writing to database
                sanitized_translate = _sanitize_null_bytes(translate)

                update_query = f"""
                                    UPDATE {self.env[record.model_id.model]._table}
                                    SET {field} = %s
                                    WHERE id = %s
                                """
                self.env.cr.execute(update_query, (json.dumps(sanitized_translate), record.record_id))

            record.status = 'revert'

    def open_record(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Linked record',
            'res_model': self.model_id.model,
            'res_id': self.record_id,
            'view_mode': 'form',
            'target': 'current',  # or 'new' to open in a popup
        }
