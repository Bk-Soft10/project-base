/** @odoo-module **/
import { bus } from "@bus/services/bus_service";
import { Component,useState, onWillUpdateProps, onWillStart } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { renderToString } from "@web/core/utils/render"
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { url } from "@web/core/utils/urls";


export class ChartUpdateButton extends Component {
    static template = "ChartUpdateButton";
setup() {
        super.setup();
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.state = useState({
            hierarchy: {},
            picking_dict:{},
            });

        const { default_event_id, active_model, active_id } = this.props.action.context;
        this.dashboard_id = active_id || (active_model === "custom.dashboard.board" && active_id);
        this.isMultiEvent = !this.dashboard_id;

        onWillStart(async () => {await this.fetchHierarchy(this.dashboard_id);
        await this.render_chart()});
        onWillUpdateProps(async (nextProps) => {
            await this.fetchHierarchy(this.dashboard_id);
        });
    }
    async fetchHierarchy(dashboard_id) {

       this.state.hierarchy = await this.orm.call("custom.dashboard.board", "get_dashboard_items_lines", [], {
            dashboard_board_id: this.dashboard_id,
        });
    }

     async delete_chart_item(event){
            var self = this;
            var chart_id = parseInt(event.currentTarget.dataset.chartItemId);
            Dialog.confirm(this, (_t("Are you sure you want to remove this item?")), {
                confirm_callback: function () {
                    self._rpc({
                        model: 'eg.custom.dashboard.item',
                        method: 'unlink',
                        args: [chart_id],
                    })
                    .then(function(result){
                       rpc('/custom_dashboard/update_chart_item_dashboard', {
                  dashboard_id: self.dashboard_board_id,
                })
                        .then(function(res){
                            self.do_action(res);
                        });
                    });
                },
            });
        }


        async edit_item_chart(event){
            var self = this;
            var chart_id = parseInt(event.currentTarget.dataset.chartItemId);
            var self = this;
            var options = {
                on_close: function () {
                    ajax.jsonRpc("/custom_dashboard/update_chart_item_dashboard", 'call', {'dashboard_id': self.dashboard_board_id})
                    .then(function(res){
                        self.do_action(res);
                    });
                },
            };
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'eg.custom.dashboard.item',
                view_id: 'ks_dashboard_ninja_list_form_view',
                views: [
                    [false, 'form']
                ],
                target: 'current',
                res_id: chart_id,
                context: {
                    'form_view_ref':'eg_ai_smart_dashboard_lite.eg_custom_dashboard_item_form_view',
                    'form_view_initial_mode': 'edit',
                },

           },options);
        }
    }
