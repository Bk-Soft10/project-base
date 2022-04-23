odoo.define('pos_multi_barcodes', function (require) {
"use strict";
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var PosDB = require('point_of_sale.DB');
    var screens = require('point_of_sale.screens');
    var _t = core._t;
    models.load_fields('product.product',['pos_multi_barcode_option']);
    models.load_models([{
        model: 'pos.multi.barcode.options',
        fields: ['name','product_id','qty','price','unit'],
        loaded: function(self,result){
            self.db.add_barcode_options(result);
            self.multi_barcode_options = result;
        },
    }],{'after': 'pos.category'});

    PosDB.include({
        init: function(options){
            var self = this;
            this.product_barcode_option_list = {};
            this._super(options);

        },
        _product_search_string: function(product){
            var str = product.display_name;
            if (product.barcode) {
                str += '|' + product.barcode;
            }
            if (product.default_code) {
                str += '|' + product.default_code;
            }
            if (product.description) {
                str += '|' + product.description;
            }
            if (product.description_sale) {
                str += '|' + product.description_sale;
            }
            var self = this;
//            var str = this._super(product);

            if(product.pos_multi_barcode_option.length > 0){
                var barcod_opt = self.product_barcode_option_list;
                for(var k=0;k<barcod_opt.length;k++){
                    for(var j=0;j<product.pos_multi_barcode_option.length;j++){
                        if(barcod_opt[k].id == product.pos_multi_barcode_option[j]){
                            if (barcod_opt[k].name) {
                                var posbarcode = barcod_opt[k].name;
                                if (posbarcode) {
                                    str += '|' + posbarcode;
                                }
                            }
                        }
                    }
                }
            }
            str  = product.id + ':' + str.replace(/:/g,'') + '\n';
            return str

        },
        add_products: function(products){
            var self = this;
            this._super(products);

            for(var i = 0, len = products.length; i < len; i++){
                var product = products[i];
                if(product.pos_multi_barcode_option){
                    var barcod_opt = self.product_barcode_option_list;
                    for(var k=0;k<barcod_opt.length;k++){
                        for(var j=0;j<product.pos_multi_barcode_option.length;j++){
                            if(barcod_opt[k].id == product.pos_multi_barcode_option[j]){
                                this.product_by_barcode[barcod_opt[k].name] = product;
                            }
                        }
                    }
                }
            }

        },
        add_barcode_options:function(barcode){
            this.product_barcode_option_list = barcode;
        },

    });
    var SuperPosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        scan_product: function(parsed_code){
            var selectedOrder = this.get_order();
            var product = this.db.get_product_by_barcode(parsed_code.base_code);

            if(!product){
                return false;
            }

            if(parsed_code.type === 'price'){
                selectedOrder.add_product(product, {price:parsed_code.value});
            }else if(parsed_code.type === 'weight'){
                selectedOrder.add_product(product, {quantity:parsed_code.value, merge:false});
            }else if(parsed_code.type === 'discount'){
                selectedOrder.add_product(product, {discount:parsed_code.value, merge:false});
            }else{
                selectedOrder.add_product(product);
            }
            var line = selectedOrder.get_last_orderline();
            var pos_multi_op = this.multi_barcode_options;
            for(var i=0;i<pos_multi_op.length;i++){
                if(pos_multi_op[i].name == parsed_code.code){
                    line.set_quantity(pos_multi_op[i].qty);
                    line.set_unit_price(pos_multi_op[i].price);
                    line.set_pro_uom(pos_multi_op[i].unit[0]);
                }
            }
            return true;
        },
    });
        var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.new_uom = '';
        },
        set_pro_uom: function(uom_id){
            this.new_uom = this.pos.units_by_id[uom_id];
            this.trigger('change',this);
        },
        get_unit: function(){
            var unit_id = this.product.uom_id;
            if(!unit_id){
                return undefined;
            }
            unit_id = unit_id[0];
            if(!this.pos){
                return undefined;
            }
            return this.new_uom == ''  ? this.pos.units_by_id[unit_id] : this.new_uom;
        },
        export_as_JSON: function(){
            var unit_id = this.product.uom_id;
            var json = _super_orderline.export_as_JSON.call(this);
            json.product_uom = this.new_uom == '' ? unit_id.id : this.new_uom.id;
            return json;
        },
        init_from_JSON: function(json){
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.new_uom = json.new_uom;
        },
    });


});

