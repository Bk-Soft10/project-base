/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { debounce } from "@web/core/utils/timing";

patch(FormController.prototype, {
    setup() {
        super.setup();
        if (this.model.root?.resModel === 'whatsapp.template') {
            this.updatePreview = debounce(this.updatePreview.bind(this), 300);
            this.setupPreviewWatcher();
        }
    },

    setupPreviewWatcher() {
        const record = this.model.root;
        if (!record || record.resModel !== 'whatsapp.template') {
            return;
        }

        console.log('WhatsApp Preview: Setting up watcher for template form');

        const previewFields = [
            'body', 'button_ids', 
            'header_type', 'footer_text', 'lang_code',
            'header_text', 'header_attachment_ids'
        ];

        // Store previous values to detect changes
        this._previousValues = {};
        for (const fieldName of previewFields) {
            if (record.fields[fieldName]) {
                this._previousValues[fieldName] = record.data[fieldName];
            }
        }

        // Use a polling approach to check for changes
        this._previewCheckInterval = setInterval(() => {
            let hasChanges = false;
            for (const fieldName of previewFields) {
                if (record.fields[fieldName]) {
                    const currentValue = JSON.stringify(record.data[fieldName]);
                    const previousValue = JSON.stringify(this._previousValues[fieldName]);
                    if (currentValue !== previousValue) {
                        hasChanges = true;
                        console.log(`WhatsApp Preview: Field ${fieldName} changed`);
                        this._previousValues[fieldName] = record.data[fieldName];
                    }
                }
            }
            if (hasChanges) {
                this.updatePreview();
            }
        }, 300); // Check every 300ms

        // Also listen to record data changes via the record's update method
        const originalRecordUpdate = record.update.bind(record);
        record.update = (changes, options) => {
            const result = originalRecordUpdate(changes, options);
            
            // Check if any preview fields changed
            if (changes) {
                const changedFields = Object.keys(changes);
                const hasPreviewField = changedFields.some(field => 
                    previewFields.includes(field) && field !== 'preview_whatsapp'
                );
                
                if (hasPreviewField) {
                    // Update previous values
                    for (const fieldName of changedFields) {
                        if (previewFields.includes(fieldName)) {
                            this._previousValues[fieldName] = record.data[fieldName];
                        }
                    }
                    // Use setTimeout to ensure the update completes first
                    setTimeout(() => {
                        this.updatePreview();
                    }, 100);
                }
            }
            
            return result;
        };
    },

    onWillUnmount() {
        super.onWillUnmount?.();
        if (this._previewCheckInterval) {
            clearInterval(this._previewCheckInterval);
        }
    },

    /**
     * Update the preview when fields change
     */
    async updatePreview() {
        const record = this.model.root;
        if (!record || record.resModel !== 'whatsapp.template') {
            return;
        }

        console.log('WhatsApp Preview: Updating preview...');

        try {
            // Get current field values from the form (including unsaved changes)
            const fieldValues = {};
            const previewFields = [
                'body', 'button_ids', 
                'header_type', 'footer_text', 'lang_code',
                'header_text', 'header_attachment_ids'
            ];

            // Read current values from the record
            for (const fieldName of previewFields) {
                if (record.fields[fieldName] !== undefined) {
                    const field = record.fields[fieldName];
                    let value = record.data[fieldName];
                    
                    if (field.type === 'one2many' || field.type === 'many2many') {
                        // For relational fields, get the current data
                        const relationData = value || [];
                        if (field.type === 'many2many') {
                            // Many2many: array of IDs
                            fieldValues[fieldName] = relationData.map(item => {
                                if (typeof item === 'object' && item.id) {
                                    return item.id;
                                }
                                return item;
                            });
                        } else {
                            // One2many: array of commands or records
                            fieldValues[fieldName] = relationData.map(item => {
                                if (typeof item === 'object') {
                                    if (item.id) {
                                        return item.id;
                                    }
                                    // Handle new records in one2many
                                    if (item.data) {
                                        return [0, 0, item.data];
                                    }
                                }
                                return item;
                            });
                        }
                    } else {
                        fieldValues[fieldName] = value;
                    }
                }
            }

            // Call RPC method with current values
            const preview = await this.env.services.orm.call(
                'whatsapp.template',
                'get_live_preview',
                [record.resId || false],
                {
                    field_values: fieldValues,
                    context: this.props.context || {},
                }
            );

            // Update the preview field - set to False if no preview (will hide the field)
            if (preview) {
                // Update the preview field directly without saving
                record.update({ preview_whatsapp: preview }, { save: false });
            } else {
                // Clear preview if no content
                record.update({ preview_whatsapp: False }, { save: false });
            }
        } catch (error) {
            console.error('Error updating preview:', error);
            // Clear preview on error
            try {
                record.update({ preview_whatsapp: False }, { save: false });
            } catch (e) {
                // Ignore errors when clearing
            }
        }
    },
});

