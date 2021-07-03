odoo.define('bsi_pos_special_price.pos_our_price', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
var utils = require('web.utils');
var round_pr = utils.round_precision;

    models.load_fields('product.product', ['our_price', 'total_saving']);

    models.load_fields('pos.order', ['our_price', 'total_saving']);

    models.load_fields('pos.order.line', ['our_price', 'total_saving']);

    var _super_Order_line = models.Orderline.prototype;


    models.Orderline = models.Orderline.extend({

    get_all_prices: function(){
        var self = this;

        var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
        var taxtotal = 0;

        var product =  this.get_product();
        var our_price = product.our_price
        var total_saving =0
        if(this.product.our_price > 0){
            total_saving = product.lst_price - product.our_price
        }
        var taxes_ids = product.taxes_id;
        var taxes =  this.pos.taxes;
        var taxdetail = {};
        var product_taxes = [];

        _(taxes_ids).each(function(el){
            var tax = _.detect(taxes, function(t){
                return t.id === el;
            });
            product_taxes.push.apply(product_taxes, self._map_tax_fiscal_position(tax));
        });

        var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
        var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), this.get_quantity(), this.pos.currency.rounding);
        _(all_taxes.taxes).each(function(tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = tax.amount;
        });

        return {
            "priceWithTax": all_taxes.total_included,
            "priceWithoutTax": all_taxes.total_excluded,
            "priceSumTaxVoid": all_taxes.total_void,
            "priceWithTaxBeforeDiscount": all_taxes_before_discount.total_included,
            "tax": taxtotal,
            "taxDetails": taxdetail,
            "our_price": our_price,
            "total_saving": total_saving,
        };
    },
    get_price_without_tax: function(){
        if(this.product.our_price > 0){
            return this.get_all_prices().our_price * this.get_quantity();
        }else{
            return this.get_all_prices().priceWithoutTax * this.get_quantity();
        }
    },
    get_total_saving: function(){
        if(this.product.our_price <= this.product.lst_price){
            return this.get_all_prices().total_saving * this.get_quantity();
        }else{
            return 0.00;
        }
    },
    });

    var _super_Order = models.Order.prototype;


    models.Order = models.Order.extend({

    /*get_total_without_tax: function() {
        return round_pr(this.orderlines.reduce((function(sum, orderLine) {
            return sum + orderLine.get_price_without_tax();
        }), 0), this.pos.currency.rounding);
    }, get_total_with_tax: function() {
            return this.get_total_without_tax() + this.get_total_tax();
        },*/

       

        initialize: function(attributes,options){
            _super_Order.initialize.call(this, attributes,options);
            this.total_saving     = null;
        },
        get_total_saving : function (){
            var total_saving = 0.00
          
            for (var i = 0; i < this.orderlines.length; i++) {
                if (this.orderlines.models[i].get_total_saving() > 0) {
                    total_saving += this.orderlines.models[i].get_total_saving()
                }
            }
            return total_saving
        },

    export_for_printing: function(){
        var orderlines = [];
        var self = this;

        this.orderlines.each(function(orderline){
            orderlines.push(orderline.export_for_printing());
        });

        var paymentlines = [];
        this.paymentlines.each(function(paymentline){
            paymentlines.push(paymentline.export_for_printing());
        });
        var client  = this.get('client');
        var cashier = this.pos.get_cashier();
        var company = this.pos.company;
        var date    = new Date();

        function is_html(subreceipt){
            return subreceipt ? (subreceipt.split('\n')[0].indexOf('<!DOCTYPE QWEB') >= 0) : false;
        }

        function render_html(subreceipt){
            if (!is_html(subreceipt)) {
                return subreceipt;
            } else {
                subreceipt = subreceipt.split('\n').slice(1).join('\n');
                var qweb = new QWeb2.Engine();
                    qweb.debug = config.isDebug();
                    qweb.default_dict = _.clone(QWeb.default_dict);
                    qweb.add_template('<templates><t t-name="subreceipt">'+subreceipt+'</t></templates>');

                return qweb.render('subreceipt',{'pos':self.pos,'widget':self.pos.chrome,'order':self, 'receipt': receipt}) ;
            }
        }

        var receipt = {
            orderlines: orderlines,
            paymentlines: paymentlines,
            subtotal: this.get_subtotal(),
            total_with_tax: this.get_total_with_tax(),
            total_without_tax: this.get_total_without_tax(),
            total_tax: this.get_total_tax(),
            total_paid: this.get_total_paid(),
            total_discount: this.get_total_discount(),
            tax_details: this.get_tax_details(),
            change: this.get_change(),
            name : this.get_name(),
            client: client ? client.name : null ,
            invoice_id: null,   //TODO
            cashier: cashier ? cashier.name : null,
            precision: {
                price: 2,
                money: 2,
                quantity: 3,
            },
            date: {
                year: date.getFullYear(),
                month: date.getMonth(),
                date: date.getDate(),       // day of the month
                day: date.getDay(),         // day of the week
                hour: date.getHours(),
                minute: date.getMinutes() ,
                isostring: date.toISOString(),
                localestring: date.toLocaleString(),
            },
            company:{
                email: company.email,
                website: company.website,
                company_registry: company.company_registry,
                contact_address: company.partner_id[1],
                vat: company.vat,
                vat_label: company.country && company.country.vat_label || '',
                name: company.name,
                phone: company.phone,
                logo:  this.pos.company_logo_base64,
            },
            currency: this.pos.currency,
            total_saving: this.get_total_saving(),
        };

        if (is_html(this.pos.config.receipt_header)){
            receipt.header = '';
            receipt.header_html = render_html(this.pos.config.receipt_header);
        } else {
            receipt.header = this.pos.config.receipt_header || '';
        }

        if (is_html(this.pos.config.receipt_footer)){
            receipt.footer = '';
            receipt.footer_html = render_html(this.pos.config.receipt_footer);
        } else {
            receipt.footer = this.pos.config.receipt_footer || '';
        }

        return receipt;
    },

    });
});
