odoo.define('sfc_pos_customize.receipt', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var rpc = require('web.rpc');
    var core = require('web.core');

    var QWeb = core.qweb;
    var _t = core._t;



var set_delivery_method = screens.ActionButtonWidget.extend({
    template: 'SetDeliveryMethodButton',
    init: function (parent, options) {
        this._super(parent, options);

        this.pos.get('orders').bind('add remove change', function () {
            this.renderElement();
        }, this);

        this.pos.bind('change:selectedOrder', function () {
            this.renderElement();
        }, this);
    },
    button_click: function () {
        var self = this;

        var no_delivery_method = [{
            label: _t("None"),
        }];
        var delivery_methods = _.map(self.pos.delivery_methods, function (delivery_method) {
            return {
                label: delivery_method.name,
                item: delivery_method
            };
        });

        var selection_list = no_delivery_method.concat(delivery_methods);
        self.gui.show_popup('selection',{
            title: _t('Select Order Type'),
            list: selection_list,
            confirm: function (delivery_method) {
                var order = self.pos.get_order();
                order.delivery_method = delivery_method;
                order.trigger('change');
            },
            is_selected: function (delivery_method) {
                return delivery_method === self.pos.get_order().delivery_method;
            }
        });
    },
    get_current_delivery_method_name: function () {
        var name = _t('Order Types');
        var order = this.pos.get_order();

        if (order) {
            var delivery_method = order.delivery_method;

            if (delivery_method) {
                name = delivery_method.name;
            }
        }
         return name;
    },
});

screens.define_action_button({
    'name': 'set_delivery_method',
    'widget': set_delivery_method,
    'condition': function(){
        return this.pos.config.enable_delivery;
    },

});

models.load_models({
    model: 'delivery.type',
    fields: ['name'],
    domain: function(self){ return [['id','in',self.config.delivery_methods]]; },
    loaded: function(self,delivery_methods){
        self.delivery_methods = delivery_methods;
    }
});


    var _super_order = models.Order;

    models.Order = models.Order.extend({
        initialize: function (attr, options) {
            _super_order.prototype.initialize.call(this, attr, options);
            this.delivery_method = this.delivery_method || false;
        },
        export_as_JSON: function(){
            var json = _super_order.prototype.export_as_JSON.apply(this,arguments);
            json.delivery_method = this.delivery_method || false;
            json.delivery_method_id  = this.delivery_method ? this.delivery_method.id : false;
            return json;
        },
        init_from_JSON: function(json){
            _super_order.prototype.init_from_JSON.apply(this,arguments);
            this.delivery_method = json.delivery_method || false;

        },
    });

});