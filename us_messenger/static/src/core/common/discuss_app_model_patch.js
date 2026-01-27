/** @odoo-module **/

import { DiscussApp } from "@mail/core/public_web/discuss_app_model";
import { fields } from "@mail/core/common/record";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(DiscussApp.prototype, {
    setup(env) {
        super.setup(...arguments);
        this.defaultMessengerCategory = fields.One("DiscussAppCategory", {
            compute() {
                return {
                    extraClass: "o-mail-DiscussSidebarCategory-messenger",
                    hideWhenEmpty: true,
                    icon: "fa fa-commenting-o",
                    id: `us_messenger.category_default`,
                    name: _t("Messengers"),
                    sequence: 40,
                };
            },
            eager: true,
        });
        this.messengerBots = fields.Many("Thread", { inverse: "appAsMessengerBots" });
    },
});
