odoo.define('era_pos_tax_invoice.qr_code', function(require) {
    "use strict";
    var PosBaseWidget = require('point_of_sale.chrome');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var utils = require('web.utils');
    var round_di = utils.round_decimals;

    var QWeb = core.qweb;
    console.log("PosBaseWidget", PosBaseWidget)

    var models = require('point_of_sale.models');

//    models.load_fields('pos.config',['allow_qr_code']);

    var module = require('point_of_sale.models');
    var models = module.PosModel.prototype.models;
    for(var i=0; i<models.length; i++){
        var model=models[i];
        if(model.model === 'res.company'){
             model.fields.push('street', 'city', 'state_id', 'country_id');
        }
    }

    screens.ReceiptScreenWidget.include({
    render_receipt: function() {
        var self = this;
        this._super();
        let order = this.pos.get_order();
//        var qr_code_data = "Company:"+this.pos.company.name;
//        if(this.pos.company.vat){
//             qr_code_data += "  | VAT NO.:"+ this.pos.company.vat;
//        }
//        if(order['formatted_validation_date']){
//            qr_code_data += "  | Order Date:"+ order['formatted_validation_date'];
//        }
//        if(order.get_total_with_tax()){
//            qr_code_data += "  | Total Amount:"+ Math.round(order.get_total_with_tax() * 100)/100;
//        }
//        if(order.get_total_tax()){
//            qr_code_data += "  | Total Tax:"+ Math.round(order.get_total_tax() * 100)/100;
//        }

        function decimalToHex(rgb) {
              var hex = Number(rgb).toString(16);
              if (hex.length < 2) {
                   hex = "0" + hex;
              }
              return hex;
            };

        function ascii_to_hexa(str)
          {
            var arr1 = [];
            str = btoa(unescape(encodeURIComponent((str))));
            str = atob(str);
            for (var n = 0, l = str.length; n < l; n ++)
             {
                var hex = Number(str.charCodeAt(n)).toString(16);
                arr1.push(hex);
             }
            return arr1.join('');
           }

        function hexToBase64(hexstring) {
            return btoa(hexstring.match(/\w{2}/g).map(function(a) {
                return String.fromCharCode(parseInt(a, 16));
            }).join(""));
        }

//        var hex_seller = ascii_to_hexa(this.env.pos.company.name);

        var hex_seller = ascii_to_hexa(this.pos.company.name);
        var len_seller = decimalToHex(hex_seller.length/2);
        var seller_name = "01"+ len_seller + hex_seller;

        var len_seller_vat = decimalToHex(this.pos.company.vat.length);
        var seller_vat_no = "02"+ len_seller_vat + ascii_to_hexa(this.pos.company.vat);

        var len_date = decimalToHex(order.creation_date.toISOString().length);
        console.log(order.creation_date.toISOString())
//                    console.log(order['formatted_validation_date'])
        var dateTime = String(order.creation_date.toISOString())
//                    dateTime = dateTime.replace("Z", " ")
        var order_date = "03"+ len_date + ascii_to_hexa(dateTime);

        var total_with_vat = Math.round(order.get_total_with_tax()*100)/100;
        var len_total = decimalToHex(String(total_with_vat).length);
        var totalWithVatHex = "04"+ len_total + ascii_to_hexa(String(total_with_vat));

        var total_vat = Math.round(order.get_total_tax()*100)/100;
        var len_total_vat = decimalToHex(String(total_vat).length);
        var totalVatHex = "05"+ len_total_vat + ascii_to_hexa(String(total_vat));

        let qrCodeValueHex = seller_name+seller_vat_no+order_date+totalWithVatHex+totalVatHex
        let qrCodeBase64 = hexToBase64(qrCodeValueHex)
        console.log(qrCodeBase64);
        console.log(qrCodeValueHex);

//        console.log(qr_code_data);
        self.qr_code = qrCodeBase64;
        new QRCode(document.getElementById("qrcode"), {"text": qrCodeBase64 ,width:200, height:200, correctLevel : QRCode.CorrectLevel.H});
    },
  });

});
