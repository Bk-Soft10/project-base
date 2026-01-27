/** @odoo-module **/

import { MessengerProject } from "./messenger_bot_model";
import { fields } from "@mail/core/common/record";
import { patch } from "@web/core/utils/patch";

const messengerProjectPatch = {
    setup() {
        super.setup(...arguments);
        this.appCategory = fields.One("DiscussAppCategory", {
            compute() {
                return {
                    extraClass: "o-mail-DiscussSidebarCategory-messenger",
                    hideWhenEmpty: !this.are_you_inside,
                    id: `us_messenger.category_${this.id}`,
                    icon: "fa fa-rocket",
                    name: this.name,
                    sequence: 22,
                };
            },
            eager: true,
            inverse: "us_messenger_project_id",
        });
        this.threads = fields.Many("Thread", { inverse: "us_messenger_project_id" });
    },
};
patch(MessengerProject.prototype, messengerProjectPatch);
