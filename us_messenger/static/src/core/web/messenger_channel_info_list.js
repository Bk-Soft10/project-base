/* @odoo-module */

import { ActionPanel } from "@mail/discuss/core/common/action_panel";
import { prettifyMessageContent } from "@mail/utils/common/format";

import { Component, useEffect, useState } from "@odoo/owl";

import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class MessengerChannelInfoList extends Component {
    static components = { ActionPanel };
    static template = "us_messenger.MessengerChannelInfoList";
    static props = ["thread"];

    setup() {
        super.setup();
        this.store = useService("mail.store");
        this.ui = useService("ui");
        this.actionService = useService("action");
        this.state = useState({ isEndingSession: false });
        useEffect(
            () => {
                if (this.props.thread.hasFetchedMessengerSessionData) {
                    return;
                }
                this.store.fetchStoreData("/us_messenger/session/data", {
                    channel_id: this.props.thread.id,
                });
                this.props.thread.hasFetchedMessengerSessionData = true;
            },
            () => [this.props.thread.id, this.props.thread.hasFetchedMessengerSessionData]
        );
    }

    onBlurNote() {
        prettifyMessageContent(this.props.thread.messengerNoteText).then((note) => {
            rpc("/us_messenger/session/update_note", { 
                channel_id: this.props.thread.id, 
                note 
            });
        });
    }

    async openClientProfile(ev) {
        ev.preventDefault();
        const clientPartner = this.props.thread?.messengerMember;
        if (!clientPartner) {
            return;
        }
        const action = {
            res_id: clientPartner.partner_id.id,
            res_model: "res.partner",
            type: "ir.actions.act_window",
            views: [[false, "form"]],
        };
        this.actionService.doAction(action);
    }

    async clickBecomeOperator() {
        await rpc("/us_messenger/operator/become", {
            channel_id: this.props.thread.id,
        });
        this.store.fetchStoreData("/us_messenger/session/data", {
            channel_id: this.props.thread.id,
        });
    }

    async endSession() {
        if (this.state.isEndingSession) {
            return;
        }
        this.state.isEndingSession = true;
        const channel_id = this.props.thread.id;
        await this.props.thread.leaveChannel({force: true});
        try {
            rpc("/us_messenger/session/end_session", {
                channel_id: channel_id,
            });
        } finally {
            this.state.isEndingSession = false;
        }
    }

    get hasClientProfile() {
        return Boolean(this.props.thread?.messenger_client_partner_id);
    }

    get hasMessengerOperator() {
        return Boolean(this.props.thread?.messenger_operator_id);
    }

    get leads() {
        return this.props.thread?.lead_ids || [];
    }

    async openLead(leadId) {
        const action = {
            res_id: leadId,
            res_model: "crm.lead",
            type: "ir.actions.act_window",
            views: [[false, "form"]],
        };
        this.actionService.doAction(action);
    }
}
