odoo.define('oi_action_trigger_reload', function (require) {
"use strict";

var core = require('web.core');

var TriggerReload = function (parent, action) {
	if (parent && parent.controllerStack) {
		var controller_id = _.last(parent.controllerStack);
		var controller = parent.controllers[controller_id];
		if (controller && controller.widget)
			controller.widget.trigger_up('reload');
	}

	return {
    	type : 'ir.actions.act_window_close'
    }
}

core.action_registry.add('trigger_reload', TriggerReload);

});