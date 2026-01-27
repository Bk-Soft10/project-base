from odoo import models, fields, api


class WhatsAppTemplate(models.Model):
    _inherit = "whatsapp.template"

    preview_whatsapp = fields.Html(
        string="Message Preview",
        compute="_compute_preview_whatsapp",
        store=False,
    )

    def _get_preview_html(self):
        """Helper method to generate preview HTML"""
        # Get interactive_types safely - field may not exist in all versions
        try:
            interactive_types = self.wa_interactive_ids if 'wa_interactive_ids' in self._fields else False
        except Exception:
            interactive_types = False
        
        return self.env['ir.qweb']._render(
            'whatsapp.template_message_preview',
            {
                'body': self._get_formatted_body(demo_fallback=True),
                'buttons': self.button_ids,
                'interactive_types': interactive_types,
                'header_type': self.header_type,
                'footer_text': self.footer_text,
                'language_direction': 'rtl' if self.lang_code in ('ar', 'he', 'fa', 'ur') else 'ltr',
            }
        )

    def _has_content(self):
        """Check if template has any content to preview"""
        # Check if there's any meaningful content
        has_body = bool(self.body and self.body.strip())
        has_buttons = bool(self.button_ids)
        has_header = bool(self.header_type and self.header_type != 'none')
        has_footer = bool(self.footer_text and self.footer_text.strip())
        
        # Check for interactive types if field exists
        has_interactive = False
        try:
            if 'wa_interactive_ids' in self._fields:
                has_interactive = bool(self.wa_interactive_ids)
        except Exception:
            pass
        
        return has_body or has_buttons or has_header or has_footer or has_interactive

    @api.depends('body', 'button_ids', 'header_type', 
                 'footer_text', 'lang_code', 'header_text', 'header_attachment_ids')
    def _compute_preview_whatsapp(self):
        """Compute preview - used for initial load and after save"""
        for record in self:
            if record and record._has_content():
                try:
                    record.preview_whatsapp = record._get_preview_html()
                except Exception:
                    record.preview_whatsapp = False
            else:
                record.preview_whatsapp = False

    @api.onchange('body', 'button_ids', 'header_type', 
                  'footer_text', 'lang_code', 'header_text', 'header_attachment_ids')
    def _onchange_preview_fields(self):
        """Trigger preview update when relevant fields change - works without save"""
        # Force recomputation by invalidating the field cache
        # This will trigger _compute_preview_whatsapp with current values
        if self:
            try:
                # Invalidate the field to force recomputation
                self.invalidate_recordset(['preview_whatsapp'])
                # Trigger recomputation (will check for content and show/hide accordingly)
                self._compute_preview_whatsapp()
            except Exception:
                pass

    @api.model
    def get_live_preview(self, template_id, field_values=None):
        """
        Method to get live preview via RPC call.
        This allows updating the preview without saving the record.
        
        :param template_id: ID of the template (False for new records)
        :param field_values: Dict of current field values from the form
        """
        field_values = field_values or {}
        
        # Create a temporary record with the current field values
        if template_id:
            template = self.browse(template_id)
            if not template.exists():
                return False
            # Start with existing record and create a new one with updated values
            # Read all relevant fields from existing record
            all_fields = set(field_values.keys())
            all_fields.update(['body', 'button_ids', 
                              'header_type', 'footer_text', 'lang_code',
                              'header_text', 'header_attachment_ids'])
            
            # Get base values from existing record
            base_values = {}
            for field_name in all_fields:
                if field_name in self._fields:
                    field = self._fields[field_name]
                    try:
                        if field.type in ('one2many', 'many2many'):
                            # For relational fields, get the recordset
                            base_values[field_name] = template[field_name].ids
                        else:
                            base_values[field_name] = template[field_name]
                    except Exception:
                        pass
            
            # Override with current field values from form
            for field_name, value in field_values.items():
                if field_name in self._fields:
                    base_values[field_name] = value
            
            # Create temporary record without saving
            template = self.new(base_values)
        else:
            # For new records, create a temporary record
            if not field_values:
                return False
            template = self.new(field_values)
        
        # Check if template has content before generating preview
        if not template._has_content():
            return False
        
        # Generate preview with current values
        try:
            # Get interactive_types safely - field may not exist in all versions
            try:
                interactive_types = template.wa_interactive_ids if 'wa_interactive_ids' in template._fields else False
            except Exception:
                interactive_types = False
            
            preview = self.env['ir.qweb']._render(
                'whatsapp.template_message_preview',
                {
                    'body': template._get_formatted_body(demo_fallback=True),
                    'buttons': template.button_ids,
                    'interactive_types': interactive_types,
                    'header_type': template.header_type,
                    'footer_text': template.footer_text,
                    'language_direction': 'rtl' if template.lang_code in ('ar', 'he', 'fa', 'ur') else 'ltr',
                }
            )
            return preview
        except Exception as e:
            return False
