odoo.define('oi_workflow.FormController', function (require) {
"use strict";

var FormController = require("web.FormController");
var session = require('web.session');
var core = require('web.core');

FormController.include({
	
	_updateButtons: function () {
		this._super.apply(this, arguments);
		var record_data = this.model.get(this.handle).data;
		
		var reject_button_name = record_data.reject_button_name;
		if (reject_button_name) {
			this.$el.find('button.oe_workflow_reject span').text(reject_button_name);
		}
		
		var approve_button_name = record_data.approve_button_name;
		if (approve_button_name) {
			this.$el.find('button.oe_workflow_approve span').text(approve_button_name);
		}				
		
		if (this.$buttons && this.mode === 'readonly') {					
			this.$buttons.find('.o_form_button_edit').toggleClass('o_hidden', !this._button_edit_enabled());
		}
	},
	
	_button_edit_enabled : function () {
		var model = this.model.get(this.handle);
		var record_data = model.data;		
		if (record_data.x_button_edit_enabled === true)
			return true;
		if (record_data.x_button_edit_enabled === false)
			return false;
		if (core.disable_edit_on_non_approval === false)
			return true;
		if (session.uid === 1 || model.context.button_edit_enabled === true)
			return true;
		if (session.uid !== 1 && model.context.button_edit_enabled === false)
			return false;
		if (record_data.state && record_data.button_approve_enabled === false)
			return false;
		return true;
	},
	_onEdit: function () {
		if (!this._button_edit_enabled())
			return;
		return this._super.apply(this, arguments);
	},
	update: function () {			
		var def = this._super.apply(this, arguments);
		var self = this;
		if (this.return_back===true) {
			def.then(function(){
				self.trigger_up('history_back');
			});
			this.return_back= false;
		}	
		return def;
	},
	
	_is_activity_list : function () {
		var context = this.model.get(this.handle).context;
		var found = false;
		_.each(context, function(v, name) {			
			if (name.indexOf('search_default_activities') === 0)
				found = true;
		});		
		return found;
	},
	
	saveRecord: function () {
		if (this._skip_save === true) {
			this._skip_save = false;
			return Promise.resolve();
		}
		return this._super.apply(this, arguments);
	},
	
	_onButtonClicked: function (event) {				
		var attrs = event.data.attrs;	
		var attrs_class = attrs.class || '';
		this.return_back = false;
		
        this._skip_save = Boolean( (attrs.skip_save || attrs.class==='oe_stat_button') && this.mode === 'readonly');        
        		
		if (attrs_class.indexOf('oe_workflow_approve') >= 0) {
			var approve_confirm_msg = this.model.get(this.handle).data.approve_confirm_msg;
			
			if (typeof approve_confirm_msg != 'undefined' && attrs.name == 'action_approve') {
				attrs.confirm = approve_confirm_msg;				
			}	
			if (this._is_activity_list()) this.return_back = true;
		}
		else if (attrs_class.indexOf('oe_workflow_reject') >= 0) {
			var record_data = this.model.get(this.handle).data;
			
			var reject_confirm_msg = record_data.reject_confirm_msg;
			
			if (typeof reject_confirm_msg != 'undefined') {
				if (!record_data.reject_button_wizard) {
					attrs.confirm = reject_confirm_msg;	
				}				
			}			
			if (this._is_activity_list()) this.return_back = true;
		}				
		
		return this._super.apply(this, arguments);
	},
});

});