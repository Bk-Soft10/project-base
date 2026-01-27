import requests
import json
import logging

from odoo import models, api, _

_logger = logging.getLogger(__name__)


class TranslationDialog(models.AbstractModel):
    _name = "translation.dialog"
    _description = "Translation Dialog"

    def _get_api_config(self):
        """Get API configuration parameters."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('otoolkit_api_key')
        api_endpoint = self.env['ir.config_parameter'].sudo().get_param('otoolkit.api.endpoint')
        return api_key, api_endpoint

    def _make_api_request(self, url, headers, payload, timeout=180):
        """Make an API request with proper error handling and logging.

        Default timeout is 180 seconds (3 minutes) to allow for OpenAI processing
        when translating to many languages.
        """
        try:
            response = requests.request(
                "POST",
                url,
                headers=headers,
                data=payload,
                timeout=timeout
            )
            return response, None
        except requests.exceptions.Timeout:
            _logger.warning("OToolKit API request timed out: %s", url)
            return None, _("The translation service is taking too long to respond. Please try again.")
        except requests.exceptions.ConnectionError as e:
            _logger.error("OToolKit API connection error: %s - %s", url, str(e))
            return None, _("Unable to connect to the translation service. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            _logger.error("OToolKit API request failed: %s - %s", url, str(e))
            return None, _("An error occurred while contacting the translation service: %s") % str(e)

    def _handle_api_response(self, response):
        """Handle API response and return appropriate result."""
        if response.status_code == 200:
            return [True, response.json(), ""]

        if response.status_code == 401:
            _logger.warning("OToolKit API authentication failed (401)")
            return [False, _("Your API key is invalid. This may be due to an input error, deletion or deactivation of the key. Please check your Otoolkit settings."), "settings"]

        if response.status_code == 400:
            try:
                error = response.json()
                error_type = error.get("type", "unknown")
                if error_type == "empty_text":
                    return [False, _("The default language text cannot be empty."), ""]
                if error_type == "insufficient_funds":
                    return [False, _("You do not have enough credits to translate. Please add credits to your balance to use this function."), "credits"]
                if error_type == "invalid_object":
                    return [False, _("No valid text fields found to translate."), ""]
                # Log unhandled 400 error types
                _logger.warning("OToolKit API returned unhandled 400 error: %s", error)
                return [False, _("Translation error: %s") % error.get("error", "Unknown error"), ""]
            except (json.JSONDecodeError, KeyError) as e:
                _logger.error("Failed to parse OToolKit API 400 response: %s", str(e))
                return [False, _("The translation service returned an invalid response."), ""]

        if response.status_code == 429:
            _logger.warning("OToolKit API rate limited (429)")
            return [False, _("Too many translation requests. Please wait a moment and try again."), ""]

        if response.status_code >= 500:
            _logger.error("OToolKit API server error (%d): %s", response.status_code, response.text[:500])
            return [False, _("The translation service is temporarily unavailable (Error %d). Please try again later.") % response.status_code, ""]

        # Log any other unexpected status codes
        _logger.error("OToolKit API unexpected status code (%d): %s", response.status_code, response.text[:500])
        return [False, _("Unexpected response from translation service (Error %d). Please try again.") % response.status_code, ""]

    def otoolkit_api_translation(self, terms, updated_terms):
        base_language = self.env.user.lang
        api_key, api_endpoint = self._get_api_config()

        if not api_key:
            return [False, _("Your API key is invalid. This may be due to an input error, deletion or deactivation of the key. Please check your Otoolkit settings."), "settings"]

        if not api_endpoint:
            _logger.error("OToolKit API endpoint not configured")
            return [False, _("The translation service is not configured. Please contact your administrator."), ""]

        payload = json.dumps({
            "terms": terms,
            "updated_terms": updated_terms,
            "base_language": base_language,
            "odoo_user_id": self.env.user.id
        })
        headers = {
            'Odoo-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        url = f"{api_endpoint}/api/auto-translate-fields/translate/"

        response, error_message = self._make_api_request(url, headers, payload)

        if error_message:
            return [False, error_message, ""]

        return self._handle_api_response(response)

    @api.model
    def translate_text(self, terms, updated_terms):
        return self.otoolkit_api_translation(terms, updated_terms)
