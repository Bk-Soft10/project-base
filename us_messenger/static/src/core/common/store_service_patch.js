/* @odoo-module */

import { Store } from "@mail/core/common/store_service";
import { _t } from "@web/core/l10n/translation";

import { patch } from "@web/core/utils/patch";

const storePatch = {
    get messengerStatusButtons() {
        return [
            {
                label: _t("In progress"),
                status: "in_progress",
                icon: "fa fa-comments",
            },
            {
                label: _t("Waiting for customer"),
                status: "waiting_customer",
                icon: "fa fa-hourglass-start",
            },
            {
                label: _t("Looking for help"),
                status: "need_help",
                icon: "fa fa-lg fa-exclamation-circle",
            },
            {
                label: _t("Without operator"),
                status: "without_operator",
                icon: "fa fa-lg fa-exclamation-circle",
            },
            {
                label: _t("End session"),
                status: "end_session",
                icon: "fa fa-flag-checkered",
            },
        ];
    },
};

patch(Store.prototype, storePatch);
