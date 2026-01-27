/** @odoo-module */

import { Record, fields } from "@mail/core/common/record";

export class MessengerNotification extends Record {
    static _name = "messenger.notification";
    static id = "id";

    /** @type {number} */
    id;
    mail_message_id = fields.One("mail.message", {
        onDelete() {
            this.delete();
        },
    });
    /** @type {string} */
    notification_type;
    /** @type {string} */
    notification_status;
    /** @type {string} */
    failure_reason;
    messenger_partner_id = fields.One("us.messenger.partner");

    get isFailure() {
        return this.notification_status === 'exception' || this.notification_status === 'canceled';
    }

    get statusIcon() {
        if (this.notification_status === 'exception') {
            return 'fa fa-exclamation text-danger';
        }
        if (this.notification_status === 'canceled') {
            return 'fa fa-ban text-muted';
        }
        if (this.notification_status === 'sent') {
            return 'fa fa-check text-success';
        }
        return 'fa fa-clock-o text-muted';
    }

    get statusTitle() {
        if (this.notification_status === 'exception') {
            return 'Failed';
        }
        if (this.notification_status === 'canceled') {
            return 'Canceled';
        }
        if (this.notification_status === 'sent') {
            return 'Sent';
        }
        return 'Ready';
    }

    get failureMessage() {
        return this.failure_reason || 'Unknown error';
    }
}

MessengerNotification.register();
