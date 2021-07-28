odoo.define('web.Sidebar.oi_action_trigger_reload', function (require) {
"use strict";

var Sidebar = require('web.Sidebar');
var core = require('web.core');
var _t = core._t;


Sidebar.include({
	
	init: function (parent, options) {		
		var self = this;		
		if (options.viewType == 'form') {
			options.actions.other.push({
				label: _t('Refresh'),
				callback: self._onReload.bind(self),
			});	
		}
		
		this._super.apply(this, arguments);				
		
	},	
	
	_onReload : function (){
		this.trigger_up('reload');
	}
});

});