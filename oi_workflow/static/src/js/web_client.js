odoo.define('web.client.oi_workflow', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session'); 

var WebClient = require("web.WebClient");

WebClient.include({
	
	load_menus: function () {
		var get_approval_models = session.rpc('/oi_workflow/approval_models', {}).then(function (data){
			core.approval_models = data.approval_models;
			core.disable_edit_on_non_approval = data.disable_edit_on_non_approval
		});
		
		var get_state_models = session.rpc('/oi_workflow/state_models', {}).then(function (data){
			core.state_models = data;
		});		
		
		var def= this._super.apply(this, arguments);
		
		return $.when(def, get_approval_models, get_state_models);
	}
});
	
		
});