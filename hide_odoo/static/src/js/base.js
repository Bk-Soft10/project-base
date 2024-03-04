/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";

patch(WebClient.prototype, "hide_odoo.WebClient", {
    setup() {
        this._super.apply(this, arguments);
        this.title.setParts({ zopenerp: "" });
    },

});

