/** @odoo-module */

import { Message } from "@mail/core/common/message_model";
import { fields } from "@mail/core/common/record";
import { patch } from "@web/core/utils/patch";

patch(Message.prototype, {
    setup() {
        super.setup();
        this.messenger_notification_ids = fields.Many("messenger.notification", {
            inverse: "mail_message_id",
        });
    },
});
