/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";

export const MessengerViewControllerMixin = (ViewController) =>
    class extends ViewController {
        setup() {
            super.setup(...arguments);
            this.store = useService("mail.store");
            this.ui = useService("ui");
        }

        async openRecord(record) {
            let channel_id = record.resId;
            if (record.resModel === "us.messenger.partner") {
                channel_id = record.data.channel_id.id;
            }
            const thread = await this.store.Thread.getOrFetch({
                model: "discuss.channel",
                id: channel_id,
            });

            if (thread) {
                return thread.open();
            }
            
            return super.openRecord(record);
        }
    };
