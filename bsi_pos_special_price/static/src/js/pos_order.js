odoo.define('bsi_pos_special_price.pos_order', function (require) {
    "use strict";
    var models = require('point_of_sale.models');

    models.load_fields('pos.order', ['discount_type', 'global_discount_amount','global_discount_percentage', 'amount_untaxed_without_discount', 'discount_amount']);

    models.load_fields('pos.order.line', ['discount_amount', 'amount_untaxed_without_discount']);

    var _super_Order = models.Order.prototype;

    models.Order = models.Order.extend({

    export_as_JSON: function() {
        var orderLines, paymentLines;
        orderLines = [];
        this.orderlines.each(_.bind( function(item) {
            return orderLines.push([0, 0, item.export_as_JSON()]);
        }, this));
        paymentLines = [];
        this.paymentlines.each(_.bind( function(item) {
            return paymentLines.push([0, 0, item.export_as_JSON()]);
        }, this));
        return {
            name: this.get_name(),
            amount_paid: this.get_total_paid() - this.get_change(),
            amount_total: this.get_total_with_tax(),
            discount_type : this.discount_type,
            global_discount_amount : this.global_discount_amount,
            global_discount_percentage: this.global_discount_percentage,
            amount_tax: this.get_total_tax(),
            amount_return: this.get_change(),
            lines: orderLines,
            statement_ids: paymentLines,
            pos_session_id: this.pos_session_id,
            pricelist_id: this.pricelist ? this.pricelist.id : false,
            partner_id: this.get_client() ? this.get_client().id : false,
            user_id: this.pos.get_cashier().id,
            uid: this.uid,
            sequence_number: this.sequence_number,
            creation_date: this.validation_date || this.creation_date, // todo: rename creation_date in master
            fiscal_position_id: this.fiscal_position ? this.fiscal_position.id : false
        };
    },


        get_total_with_tax: function() {
            this.get_discount_amount()
            return this.get_total_without_tax() + this.get_total_tax() - this.get_discount_amount();
        },

        initialize: function(attributes,options){
            _super_Order.initialize.call(this, attributes,options);
            this.discount_type     = null;
            this.global_discount_percentage = null;
            this.global_discount_amount = null;
            this.amount_untaxed_without_discount = null;
            this.discount_amount = null;
        },
        get_discount_amount : function (){
            var discount_amount = 0.00
            var price_without_tax = 0.00
            var discount_type = this.discount_type;
            var global_discount_percentage = this.global_discount_percentage;
            var global_discount_amount = this.global_discount_amount;
          
            for (var i = 0; i < this.orderlines.length; i++) {
                if (this.orderlines.models[i].get_price_without_tax() > 0) {
                    price_without_tax = price_without_tax + (this.orderlines.models[i].get_price_without_tax())
                }
            }
            if(discount_type == "2"){
                discount_amount = (price_without_tax * global_discount_percentage)/100
            }
            if(discount_type == "1"){
                discount_amount = global_discount_amount
            }
            this.discount_amount = discount_amount
            return discount_amount
        },
    });
});

