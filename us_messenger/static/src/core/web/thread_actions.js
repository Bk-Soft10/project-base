/* @odoo-module */

import { registerThreadAction } from "@mail/core/common/thread_actions";
import { _t } from "@web/core/l10n/translation";
import { usePopover } from "@web/core/popover/popover_hook";
import { MessengerChannelInfoList } from "@us_messenger/core/web/messenger_channel_info_list";
import { MessengerCommandDialog } from "@us_messenger/core/web/messenger_command_dialog";

const MESSENGER_CHANNEL_TYPES = ["telegram", "viber", "whatsapp", "facebook", "instagram"];

registerThreadAction("messenger-info", {
    actionPanelComponent: MessengerChannelInfoList,
    condition: ({ owner, thread }) =>
        thread && thread.channel_type?.startsWith('us_messenger_') && !owner.isDiscussSidebarChannelActions,
    panelOuterClass: "o-messenger-ChannelInfoList bg-inherit",
    icon: "fa fa-fw fa-info",
    name: _t("Information"),
    sequence: 10,
    sequenceGroup: 7,
    toggle: true,
});

registerThreadAction("messenger-status", {
    actionPanelComponent: MessengerChannelInfoList,
    condition: ({ owner, thread }) =>
        thread && thread.channel_type?.startsWith('us_messenger_') && !thread.messenger_end_dt && !owner.isDiscussContent,
    dropdown: true,
    dropdownMenuClass: "p-0",
    dropdownTemplate: "us_messenger.MessengerStatusSelection",
    dropdownTemplateParams: ({ thread }) => ({ messengerThread: thread }),
    panelOuterClass: "o-messenger-ChannelInfoList bg-inherit",
    icon: ({ store, thread }) => {
        const btn = store.messengerStatusButtons.find(
            (btn) => btn.status === thread.messenger_status
        );
        if (!btn) {
            return undefined;
        }
        return {
            template: "us_messenger.MessengerStatusLabel",
            params: { btn, inThreadActions: true },
        };
    },
    name: ({ thread }) => thread.messengerStatusLabel,
    nameClass: "fst-italic small",
    sequence: ({ owner }) => (owner.isDiscussSidebarChannelActions ? 10 : 5),
    sequenceGroup: ({ owner }) => (owner.isDiscussSidebarChannelActions ? 5 : 7),
    toggle: true,
});

registerThreadAction("messenger-create-lead", {
    actionPanelComponent: MessengerCommandDialog,
    actionPanelComponentProps: ({ action }) => ({
        close: () => action.close(),
        commandName: "messenger_lead",
        placeholderText: _t("e.g. Product pricing"),
        title: _t("Create Lead"),
        icon: "fa fa-handshake-o",
    }),
    close: ({ action }) => action.popover?.close(),
    condition: ({ owner, thread, store }) =>
        thread?.channel_type?.startsWith('us_messenger_') &&
        store.has_access_create_lead &&
        !owner.isDiscussSidebarChannelActions,
    panelOuterClass: "bg-100",
    icon: "fa fa-handshake-o",
    name: _t("Create Lead"),
    sequence: 15,
    sequenceGroup: 25,
    setup({ owner }) {
        if (!owner.env.inChatWindow) {
            this.popover = usePopover(MessengerCommandDialog, {
                onClose: () => this.close(),
                popoverClass: this.panelOuterClass,
            });
        }
    },
    toggle: true,
    open({ owner, thread }) {
        this.popover?.open(owner.root.el.querySelector(`[name="${this.id}"]`), {
            thread,
            ...this.actionPanelComponentProps,
        });
    },
});
