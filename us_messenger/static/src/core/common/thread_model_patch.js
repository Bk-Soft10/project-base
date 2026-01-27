/** @odoo-module **/

import { Thread } from "@mail/core/common/thread_model";
import { fields } from "@mail/core/common/record";
import { patch } from "@web/core/utils/patch";


patch(Thread.prototype, {
    setup() {
        super.setup(...arguments);
        this.appAsMessengerBots = fields.One("DiscussApp", {
            compute() {
                return this.channel_type?.startsWith("us_messenger_") ? this.store.discuss : null;
            },
        });
        this.us_messenger_project_id = fields.One("us.messenger.project", { inverse: "threads" });
        this.messengerOperator = fields.One("res.partner");
        this.lead_ids = fields.Many("crm.lead");
        this.messengerMember = fields.One("discuss.channel.member", {
            compute() {
                if (this.channel_type && !this.channel_type.startsWith("us_messenger_")) {
                    return;
                }
                // For livechat threads, the correspondent is the first
                // channel member that is not the operator.
                const orderedChannelMembers = [...this.channel_member_ids].sort(
                    (a, b) => a.id - b.id
                );
                const isFirstMemberOperator = orderedChannelMembers[0]?.partner_id?.eq(
                    this.messengerOperator
                );
                const messenger_client = isFirstMemberOperator
                    ? orderedChannelMembers[1]
                    : orderedChannelMembers[0];
                return messenger_client;
            },
        });
    },
    _computeDiscussAppCategory() {
        if (!this.channel_type?.startsWith("us_messenger_")) {
            return super._computeDiscussAppCategory();
        }
        return this.us_messenger_project_id?.appCategory ?? this.appAsMessengerBots?.defaultMessengerCategory;
    },
    get avatarUrl() {
        if (this.channel_type && this.channel_type.startsWith("us_messenger_") && this.correspondent) {
            return this.correspondent.avatarUrl;
        }
        return super.avatarUrl;
    },
    /** @returns {import("models").ChannelMember} */
    computeCorrespondent() {
        if (this.channel_type && !this.channel_type.startsWith("us_messenger_")) {
            return super.computeCorrespondent();
        }
        return this.messengerMember;
    },
});
