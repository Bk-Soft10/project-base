odoo.define('web.Sidebar.oi_workflow', function (require) {
"use strict";

var Sidebar = require('web.Sidebar');
var Dialog = require('web.Dialog');
var core = require('web.core');
var session = require('web.session');

var Context = require('web.Context');
var pyUtils = require('web.py_utils');

var _t = core._t;
var qweb = core.qweb;


Sidebar.include({
	
	init: function (parent, options) {		
		var self = this;		
		if (options.viewType == 'form' && _.contains(core.approval_models, parent.modelName)) {
			options.actions.other.push({
				label: _t('Approval Info'),
				callback: self._onApprovalInfo.bind(self),
			});	
		}
		if ( !(options.viewType == 'form') && _.contains(core.approval_models, parent.modelName)) {
			options.actions.other.push({
				label: _t('Approve'),
				callback: self._onApprove.bind(self),
			});	
		}
				
		if ( odoo.debug && session.is_system && _.contains(core.state_models, parent.modelName)) {
			options.actions.other.push({
				label: _t('Update Status'),
				callback: self._onUpdateStatus.bind(self),
			});	
		}
		
		this._super.apply(this, arguments);				
		
	},	
	_onUpdateStatus : function () {		
		var self = this;
		self.trigger_up('sidebar_data_asked', {
            callback: function (env) {
            	self.env = env;
                var activeIdsContext = {
                    active_id: env.activeIds[0],
                    active_ids: env.activeIds,
                    active_model: env.model,
                };
                if (env.domain) {
                    activeIdsContext.active_domain = env.domain;
                }

                var context = pyUtils.eval('context', new Context(env.context, activeIdsContext));
                self.do_action({
                    name: 'Change Document Status',
                    res_model: 'approval.state.update',
                    type: 'ir.actions.act_window',
                    views: [[false, 'form']],
                    view_type: 'form',
                    view_mode: 'form',
                    target : 'new',
                    context : context
                });
            }
		});
	},
	
	_onApprove: function () {		
		var self = this;
        Dialog.confirm(this, (_t("Are you sure you want to approve selected documents?")), {
            confirm_callback: function () {
                self.trigger_up('sidebar_data_asked', {
                    callback: function (env) {
                        self.env = env;
                        var activeIdsContext = {
                            active_id: env.activeIds[0],
                            active_ids: env.activeIds,
                            active_model: env.model,
                        };
                        if (env.domain) {
                            activeIdsContext.active_domain = env.domain;
                        }

                        var context = pyUtils.eval('context', new Context(env.context, activeIdsContext));
                        self._rpc({
                            route: '/web/dataset/call_button',
                            params: {
                                args: [self.env.activeIds],
                                method : 'action_approve',
                                model : self.env.model,
                                kwargs : {},
                                context : self.env.context
                            },
                        }).then(function (result) {
                        	 self.trigger_up('reload');
                        });
                    }
                });
            	 
            },
        });
		
	},
	_onApprovalInfo : function () {		
		var activeId = this.env.activeIds[0];
		var self = this;
		if (activeId) {
			session.rpc('/oi_workflow/approval_info', {model : self.env.model, record_id : activeId, context : this.env.context}).then(function (data){
		        var buttons = [
		        	{
		        		text: _t("Ok"), 
		        		close: true,
		        		classes: 'btn-primary',
		        	}
		        ];
		        		        				
				new Dialog(self, {
	                title: _t("Approval Info"),
	                size: 'medium',
	                buttons : buttons,
	                $content: qweb.render('oi_workflow.approval_info', {
	                	data : data,
	                	session : session,
	                	odoo : odoo
	                })
	            }).open();
			});
		}
	}	
	
});

});