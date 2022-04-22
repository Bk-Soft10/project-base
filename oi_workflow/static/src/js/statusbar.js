odoo.define('oi_workflow.statusbar', function (require) {
"use strict";

var FieldStatus = require('web.relational_fields').FieldStatus;

FieldStatus.include({
	
	_setState: function () {
		var statusbar_visible = this.attrs.statusbar_visible || 'WORKFLOW'; 
		if (_.str.startsWith(statusbar_visible ,'WORKFLOW') && this.record.data.workflow_states) {
			var workflow_states = JSON.parse(this.record.data.workflow_states);
			var other_states = statusbar_visible.split(",");
			var selection = this.field.selection;
			var self = this;
            selection = _.filter(selection, function (val) {
                return _.contains(workflow_states, val[0]) || val[0] === self.value || _.contains(other_states, val[0]);
            });
            this.status_information = _.map(selection, function (val) {
                return { id: val[0], display_name: val[1], selected: val[0] === self.value, fold: false };
            });
            return;			
		}
		return this._super.apply(this, arguments); 
	}
	
});

});