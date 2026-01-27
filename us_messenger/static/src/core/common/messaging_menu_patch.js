import { MessagingMenu } from "@mail/core/public_web/messaging_menu";

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(MessagingMenu.prototype, {
    /**
     * @override
     */
    get _tabs() {
        const items = super._tabs;
        const hasMessengers = Object.values(this.store.Thread.records).some(
            ({ channel_type }) => channel_type.startwith("us_messenger_")
        );
        if (hasMessengers) {
            items.push({
                counter: this.store.discuss.messengerBots.reduce(
                    (acc, channel) =>
                        channel.self_member_id?.message_unread_counter > 0 ? acc + 1 : acc,
                    0
                ),
                id: "messenger",
                icon: "fa fa-commenting-o",
                activeIcon: "fa fa-commenting",
                label: _t("Messenger Chats"),
                sequence: 60,
            });
        }
        return items;
    },
});
