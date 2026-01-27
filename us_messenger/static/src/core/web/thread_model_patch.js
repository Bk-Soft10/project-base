/* @odoo-module */

import { Thread } from "@mail/core/common/thread_model";
import { Record } from "@mail/core/common/record";
import { fields } from "@mail/model/misc";
import { convertBrToLineBreak } from "@mail/utils/common/format";
import { rpc } from "@web/core/network/rpc";

import { patch } from "@web/core/utils/patch";


patch(Thread.prototype, {
    setup() {
        super.setup();
        this.messenger_note = fields.Html();
        this.messengerNoteText = fields.Attr(undefined, {
            compute() {
                if (this.messenger_note !== undefined) {
                    return convertBrToLineBreak(this.messenger_note || "");
                }
                return this.messengerNoteText;
            },
        });
    },
    /** @type {MessengerRecipient[]} */
    messengerRecipients: [],
    messenger_status: "",
    messenger_end_dt: false,
    hasFetchedMessengerSessionData: false,

    get isChatChannel() {
        return this.channel_type?.startsWith("us_messenger_") || super.isChatChannel;
    },

    get hasMemberList() {
        return this.channel_type?.startsWith("us_messenger_") || super.hasMemberList;
    },

    get canUnpin() {
        return this.channel_type?.startsWith("us_messenger_") || super.hasMemberList;
    },

    get messengerStatusLabel() {
        const statusMap = {
            'in_progress': 'In progress',
            'waiting_customer': 'Waiting for customer',
            'need_help': 'Looking for help', 
            'without_operator': 'Without operator',
            'end_session': 'End session',
        };
        return statusMap[this.messenger_status] || '';
    },

    updateMessengerStatus(status) {
        if (this.messenger_status === status) {
            return;
        }
        this.messenger_status = status;
        rpc("/us_messenger/session/update_status", {
            channel_id: this.id,
            status: status,
        });
    },
});
