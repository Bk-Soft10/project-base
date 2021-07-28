odoo.define('oi_mail.systray.ActivityMenu', function (require) {
"use strict";

var ActivityMenu = require("mail.systray.ActivityMenu");
var session = require('web.session');
var core = require('web.core');
var Menu = require("web.Menu");

ActivityMenu.include({
    
	/**
     * Redirect to particular model view
     * @private
     * @param {MouseEvent} event
     */
    _onActivityFilterClick: function (event) {
        // fetch the data from the button otherwise fetch the ones from the parent (.o_mail_preview).
        var data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
        var context = {};
        if (data.filter === 'my') {
            context['search_default_activities_overdue'] = 1;
            context['search_default_activities_today'] = 1;
        } else {
            context['search_default_activities_' + data.filter] = 1;
        }
        var main_menu_id = 0;
        _.each(this._activities, function(activity_data){
        	if (activity_data.model ==data.res_model)
        		main_menu_id = activity_data.main_menu_id;
        });
        core.bus.trigger('change_menu_section', main_menu_id);
        this.do_action({
            type: 'ir.actions.act_window',
            name: data.model_name,
            res_model:  data.res_model,
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            search_view_id: [false],
            domain: [['activity_user_id', '=', session.uid]],
            context:context,
            target : 'main'
        }, {
        	clear_breadcrumbs : true
    	});
    },
	
});

});