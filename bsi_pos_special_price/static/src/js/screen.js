odoo.define('bsi_pos_special_price.screen', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');

    var OrderWidget = screens.OrderWidget.include({
        update_summary: function(){
            var order = this.pos.get_order();
            if (!order.get_orderlines().length) {
                return;
            }
            var total_saving =  order ? order.get_total_saving() : 0;
            var total     = order ? order.get_total_with_tax() : 0;
            var taxes     = order ? order.get_total_with_tax() - order.get_total_without_tax() : 0;
            this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
            this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);
            this.el.querySelector('.summary .total-saving .total-saving-value').textContent = this.format_currency(total_saving);
        },
    });
});

