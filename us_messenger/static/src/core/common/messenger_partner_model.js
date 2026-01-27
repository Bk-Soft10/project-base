/** @odoo-module */

import { Record, fields } from "@mail/core/common/record";

export class MessengerPartner extends Record {
    static _name = "us.messenger.partner";
    static id = "id";

    /** @type {number} */
    id;
    /** @type {string} */
    name;
    /** @type {string} */
    type_messenger;
    bot_id = fields.One("us.messenger.project");
}

MessengerPartner.register();
