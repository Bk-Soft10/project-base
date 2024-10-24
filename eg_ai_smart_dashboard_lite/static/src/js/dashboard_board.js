odoo.define('eg_ai_smart_dashboard_lite.dashboard_board', function (require) {
"use strict";
    var AbstractAction = require('web.AbstractAction');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var viewRegistry = require('web.view_registry');
    var _t = core._t;
    var QWeb = core.qweb;
    var utils = require('web.utils');
    var session = require('web.session');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');

    var CustomDashboardBoard =  AbstractAction.extend({
        contentTemplate: 'CustomDashboardBoard',

        events: {
            'click #save_dashboard': 'save_dashboard_data',
            'click #chart-type-selection > span': 'add_chart_item',
            'click #edit_dashboard': 'edit_dashboard',
            'click #search-button': 'search_chart',
            'click #searchclear': 'clear_search',
            'click .delete-item-chart': 'delete_chart_item',
            'click .edit-item-chart': 'edit_item_chart',
            'click #back_kanaban_view': 'back_history',
            'click .menu-icon': 'open_sidebar_menu',
            'click .close-sidebar': 'close_sidebar_menu',
        },

        init: function(parent, action) {
            var self= this;
            if (action.context.active_id){
                self.dashboard_board_id = action.context.active_id;
            }
            else{
               self.dashboard_board_id = action.params.dashboard_board_id;
            }
            this._super.apply(this, arguments);
        },

        willStart: function () {
            var self = this;
            var def = this._rpc({
                    model: 'custom.dashboard.board',
                    method: 'get_dashboard_items_lines',
                    args: [self.dashboard_board_id],
                })
                .then(function (res) {
                     self.dashboard_data = res;
                });

            return Promise.all([
                this._super.apply(this, arguments),def
            ]);
        },

        start: function () {
            var self = this;
            var options = {};
            self._render_chart();
            return this._super();
        },
        delete_chart_item: function(event){
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
                        ajax.jsonRpc("/custom_dashboard/update_chart_item_dashboard", 'call', {'dashboard_id': self.dashboard_board_id})
                        .then(function(res){
                            self.do_action(res);
                        });
                    });
                },
            });
        },

        edit_item_chart: function(event){
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
        },

        add_chart_item: function(event){
            var self = this;
            console.log(event.currentTarget);
            var chart_type = event.currentTarget.dataset.chartType;
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
                view_id: 'custom_dashboard_form_view',
                views: [
                    [false, 'form']
                ],
                target: 'new',
                context: {
                    'custom_dashboard_board_id': self.dashboard_board_id,
                    'chart_type': chart_type,
                    'form_view_ref': 'eg_custom_dashboard_item_form_view',
                    'form_view_initial_mode': 'edit',
                },
            },options);
        },

        back_history: function(event){
         var self = this;
         this.do_action('eg_ai_smart_dashboard_lite.action_custom_dashboard_board');
        },
        open_sidebar_menu:function(){
             var self = this;
             $('#sidebar-wrapper').addClass('openSideBar');
             $('.close-sidebar').addClass('close-icon');
             $('.navbar-toggler-icon').addClass('remove-icon');
             $('.menu-icon').addClass('menu-icon-none');
        },
        close_sidebar_menu:function(){
            $('#sidebar-wrapper').removeClass('openSideBar');
            $('.menu-icon').removeClass('menu-icon-none');
            $('.close-icon').removeClass('close-icon');
        },
        clear_search: function(){
            var self = this;
            self.$("#search-input-chart").val('');
            ajax.jsonRpc("/custom_dashboard/remove_search_chart", 'call', {'dashboard_item_id': self.dashboard_board_id})
            .then(function(res){
               self.$(".grid-stack").remove();
                self.$(".container-fluid-dashboard").append("<div class='grid-stack' id='grid-stack'></div>")
                self.dashboard_data = res;
                self._render_chart();
            });
        },

        change_chart_search: function(){
            var self = this;
            var search_input = self.$("#search-input-chart").val();
            ajax.jsonRpc("/custom_dashboard/search_input_chart", 'call', {'search_input': search_input, 'dashboard_item_id': self.dashboard_board_id})
            .then(function(res){
                self.$(".grid-stack").remove();
                self.$(".container-fluid-dashboard").append("<div class='grid-stack' id='grid-stack'></div>")
                self.dashboard_data = res;
                self._render_chart();
            });
        },

        search_chart: function(){
            var self = this;
            var search_input = self.$("#search-input-chart").val();
            ajax.jsonRpc("/custom_dashboard/search_input_chart", 'call', {'search_input': search_input, 'dashboard_item_id': self.dashboard_board_id})
            .then(function(res){
                self.$(".grid-stack").remove();
                self.$(".container-fluid-dashboard").append("<div class='grid-stack search-action' id='grid-stack'></div>");
                self.$(".container-fluid-dashboard").addClass("search-action-container");
                self.$(".main-container").addClass("main-search-container");
                self.dashboard_data = res;
                self._render_chart();
            });
        },

        save_dashboard_data: function(event){
            var self = this;
            self.grid.enableMove(false, true);
            self.grid.enableResize(false, true);
            var data_list = []
            self.$('.chart-container').each(function(){
                var data_obj = {
                    'item_id': this.getAttribute('data-gs-id'),
                    'chart_height': parseFloat(this.getAttribute('data-gs-height')),
                    'chart_width': parseFloat(this.getAttribute('data-gs-width')),
                    'chart_x': parseFloat(this.getAttribute('data-gs-x')),
                    'chart_y': parseFloat(this.getAttribute('data-gs-y')),
                }
                 data_obj.item_id = parseFloat(data_obj.item_id.slice(11))
                 data_list.push(data_obj);

            })
            ajax.jsonRpc("/custom_dashboard/dashboard_configuration", 'call', {'data_list': JSON.stringify(data_list)})
//            self.$(event.target).hide();
////            self.$("#edit_dashboard").show();
//            self.$("#dashboard_template_name").show();
//            self.$("#dashboard_template_name_input").hide();
            var dashboard_template_name = self.$('#dashboard_template_name_input').val();
            ajax.jsonRpc("/custom_dashboard/dashboard_template_name", 'call', {'dashboard_id': self.dashboard_board_id, 'template_name': dashboard_template_name})
            .then(function(result){
                self.$("#dashboard_template_name").text(result);
                self.$("#dashboard_template_name_input").val(result);
            });
//                         window.addEventListener('resize',function(){
//              data_list.resize();
//            });
             $(document).on("click", "#save_dashboard", function(event){
                $(".my-hover-list").removeClass('action-btn');
                $(".chart-container").removeClass('shake-effect');
                 $(".action-menu-list").removeClass('show-save');
                  $(".action-menu-list").addClass('show-edit');

            });
        },
        edit_dashboard: function(){
            var self = this;
            self.grid.enableMove(true, false);
            self.grid.enableResize(true, false);
            $(document).on("click", "#edit_dashboard", function(event){
                $(".my-hover-list").addClass('action-btn');
                $(".chart-container").addClass('shake-effect');
                $(".action-menu-list").addClass('show-save');
                $(".action-menu-list").removeClass('show-edit');
            });

        },

        _render_chart: function(){
            var self = this;
            var options = {};
            self.dashboard_data.dashboard_item_ids.forEach(function (dashboard_item_id) {
                ajax.jsonRpc("/custom_dashboard/get_dashboard_items_data", 'call', {'dashboard_item_id': dashboard_item_id})
                .then(function (res) {
                    if (['kpi','tiles'].includes(res.chart_type)){
                        self.generate_kpi_or_tiles(res,dashboard_item_id)
                    }
                    else if (res.chart_type == 'list'){
                        self.generate_list_view(res,dashboard_item_id)
                    }

                    else{
                        self.generate_graph(res, dashboard_item_id);
                    }
                });
            });
        },


        generate_kpi_or_tiles: function(dict_data, dashboard_item_id){
            var self = this;
            var dataset = JSON.parse(dict_data.chart_data);
            var grid_path = null;
            var new_grid = null;
            var options_grid = {
                alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
                staticGrid: true,
                float: false,
                margin: '100px',
            };
            self.$('.grid-stack').gridstack(options_grid);
            var grid_stack = self.$('.grid-stack');
            self.grid = self.$('.grid-stack').data('gridstack');
            self.grid.enableMove(false, true);
            self.grid.enableResize(false, true);
            grid_stack.append(`<div class='chart-container box tile-box' id='chart_item_${dashboard_item_id}' /></div>`)
            var serizize_data = null;
            if (dict_data.chart_dashboard_positions){
                var dict_obj = JSON.parse((dict_data.chart_dashboard_positions))
                serizize_data = [{id: `chart_item_${dashboard_item_id}`, x: dict_obj.chart_x, y: dict_obj.chart_y, w: dict_obj.chart_width, h:dict_obj.chart_height,maxHeight:2, minHeight:2,minWidth:2}]
            }
            else{
                serizize_data = [{id: `chart_item_${dashboard_item_id}`, x: 0, y: 200, w: 3, h:4,maxHeight:2,minHeight:2,minWidth:2}]
            }
            var items = GridStackUI.Utils.sort(serizize_data);
            items.forEach(node=>{
                var containerElt = $("#" + node.id);
                containerElt.attr("data-gs-id", node.id);
                containerElt.attr("data-gs-width", node.w);
                containerElt.attr("data-gs-height", node.h);
                containerElt.attr("data-gs-x", node.x);
                containerElt.attr("data-gs-y", node.y);
                containerElt.attr("data-gs-max-height", node.maxHeight);
                containerElt.attr("data-gs-min-height", node.minHeight);
                containerElt.attr("data-gs-min-width", node.minWidth);
                grid_path = self.grid.makeWidget(containerElt)
            });
            var image_src = session.url('/web/image', {
                model: dict_data.model_name,
                id: dict_data.id,
                field: "tile_image_selection",
            });
            var dataset = JSON.parse(dict_data.chart_data)
            var render_data={
                'layout':dict_data.tile_kpi_layout,
                'background_color':dict_data.chart_background_color,
                'text_color': dict_data.chart_fore_color,
                'icon_bgcolor':dict_data.icon_bgcolor,
                'title_font': dict_data.title_font,
                'icon_color':dict_data.icon_color,
                'tile_image_type': dict_data.tile_image_type,
                'tile_icon': dict_data.tile_icon,
                'title':  dict_data.name,
                'image_url': image_src,
                'id': dict_data.id,
                'tile_unit': dict_data.tile_unit || '',
            }

            var template_id = 'KpiTile'
            if (dict_data.chart_type == "kpi"){

                render_data['value']=dataset
                 render_data['kpi_model_id']=dict_data.kpi_model_id
                 render_data['kpi_data_calculation_type']=dict_data.kpi_data_calculation_type

            }
            else{
                 render_data['value']=dataset.total

//                 var tile_data={
//                 'value': dataset,
//                 'kpi_model_id': dict_data.kpi_model_id,
//                 'kpi_data_calculation_type': dict_data.kpi_data_calculation_type,
//                 }
//                render_data.forEach(({ key, val }) => key in tile_data ? tile_data[key].push(val) : tile_data[key] = [val] )

            }
            var $chartContainer = $(QWeb.render(template_id, render_data));
            var update_button_container = $(QWeb.render('ChartUpdateButton', {
                'id': dict_data.id,
            }));
            var new_chart = self.$(".grid-stack").find(`[id='chart_item_${dashboard_item_id}']`)
            new_chart.append('<div class="grid-stack-item-content tile-kpi-shadow"></div>')
            var new_grid_item = self.$(".grid-stack").find(`[id='chart_item_${dashboard_item_id}']`).find('.grid-stack-item-content');
            new_grid_item.prepend($chartContainer);
            new_grid_item.prepend(update_button_container);
        },

        generate_graph: function(dict_data, dashboard_item_id){
            var self = this;
            var dataset = JSON.parse(dict_data.chart_data);
            var grid_path = null;
            var new_grid = null;
            var options_grid = {
                alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
                staticGrid: true,
                float: false,
                margin: '100px',
            };
            self.$('.grid-stack').gridstack(options_grid);
            var grid_stack = self.$('.grid-stack');
            self.grid = self.$('.grid-stack').data('gridstack');
            self.grid.enableMove(false, true);
            self.grid.enableResize(false, true);
            var xyz=grid_stack.append(`<div class='chart-container box' id='chart_item_${dashboard_item_id}' /></div>`)
            var new_chart = self.$(".grid-stack").find(`[id='chart_item_${dashboard_item_id}']`)
            var abc= new_chart.append(`<div class="grid-stack-item-content" style="width:98%;height:100%;"></div>`)
            var new_grid_item = self.$(".grid-stack").find(`[id='chart_item_${dashboard_item_id}']`).find('.grid-stack-item-content')
//             if(dict_data.chart_theme ) {
               var myChart = echarts.init(new_grid_item[0],dict_data.chart_theme);
//            }
//            else{
//                  var myChart = echarts.init(new_grid_item[0]);
//            }
//            var myChart = echarts.init(new_grid_item[0]);
//            myChart.resize()
//            grid_stack.append(`<div class='chart-container box' id='chart_item_${dashboard_item_id}' /></div>`)
            var serizize_data = null;
            if (dict_data.chart_dashboard_positions){
                var dict_obj = JSON.parse((dict_data.chart_dashboard_positions))
                serizize_data = [{id: `chart_item_${dashboard_item_id}`, x: dict_obj.chart_x, y: dict_obj.chart_y, w: dict_obj.chart_width, h:dict_obj.chart_height}]

            }
            else{
                serizize_data = [{id: `chart_item_${dashboard_item_id}`, x: 0, y: 200, w: 5, h:5}]
            }

            var items = GridStackUI.Utils.sort(serizize_data);
            items.forEach(node=>{
                var containerElt = $("#" + node.id);
                containerElt.attr("data-gs-id", node.id);
                containerElt.attr("data-gs-width", node.w);
                containerElt.attr("data-gs-height", node.h);
                containerElt.attr("data-gs-x", node.x);
                containerElt.attr("data-gs-y", node.y);
                grid_path = self.grid.makeWidget(containerElt)

            });

            var options = {
                title: {
                    text:dict_data.name,
                    left:'center',
                    padding: [10, 0, 0, 0],
                },
                backgroundColor: dict_data.chart_background_color,
                grid: {
				show: dict_data.is_show_grid,
                width: 'auto' ,
                height: 'auto' ,
                backgroundColor: dict_data.grid_bg_color ,
                borderColor: dict_data.grid_color ,
                borderWidth: dict_data.grid_border_width,
                shadowBlur: dict_data.grid_shadow_blur ,
                shadowColor: dict_data.grid_shadow_color ,

			    },
                animationType: 'scale',
                animationEasing: dict_data.animation_easing_type,
                animationDuration:dict_data.animation_speed,
                animationDelay: function (idx) {
                    return Math.random() * dict_data.animation_gradually_delay;
                 },
                //declare outside for comman
                toolbox: [{
                    show: true,
                    feature: {
                        mark: { show: true },
                        dataView: { show: true, readOnly: false },
                        estore: { show: true },
                        saveAsImage: { show: true }
                    },
                    left:'5px'
                  }],
                };
             if (dict_data.chart_type == 'bar'){
                if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'left'){
                            options['legend'] = {
                                     data: dataset.name,
                                    left: 'top'

                                }
                            }

                else if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'right'){
                            options['legend'] = {
                                     data: dataset.name,
                                    right: 'top'

                                }
                            }
                else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'left'){
                            options['legend'] = {
                                     data: dataset.name,
                                    left: 'left'

                                }
                            }
                else if (dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'right'){
                            options['legend'] = {
                                     data: dataset.name,
                                    right: 'right'

                                }
                            }
                else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'right' || dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'left'){
                            options['legend'] = {
                                     data: dataset.name,
                                    left: 'right'
                                }
                            }
                else if (dict_data.legend_position == 'bottom' || dict_data.legend_horizontal_align == 'right' || dict_data.legend_horizontal_align == 'right'){
                            options['legend'] = {
                                     data: dataset.name,
                                    bottom: 'left'

                                }
                            }
                else{
                options['legend'] = {
                                     data: dataset.name,
                                    top :'bottom'

                                }
                }
                options['tooltip'] = {
					trigger: 'axis'

				},
			options['xAxis'] = {
					type: 'value',
				},
			options['yAxis'] = {

					type: 'category',
//                    boundaryGap: false,
    				data: dataset.model_label_list,

				},
			options['series'] = dataset.data_list
            }
            if (dict_data.chart_type == 'polarArea'){
                     options['legend'] = {
					 data: dataset.name,
					top: 'bottom'
				},
			    options['polar'] = {
					radius: [10, '80%']
				},
				options['angleAxis'] = {
					max: dataset.max * 1.1,
					startAngle: 75
				},
				options['radiusAxis'] = {
					type: 'category',
					data: dataset.model_label_list
				},
				options['tooltip'] = {},
				options['series'] = dataset.data_list
            }
            if (dict_data.chart_type == 'column'){
                   if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'left'){
                            options['legend'] = {
                                     data: dataset.name,
                                    left: 'top'

                                }
                            }

                else if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'right'){
                            options['legend'] = {
                                     data: dataset.name,
                                    right: 'top'

                                }
                            }
                else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'left'){
                            options['legend'] = {
                                     data: dataset.name,
                                    left: 'left'

                                }
                            }
                else if (dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'right'){
                            options['legend'] = {
                                     data: dataset.name,
                                    right: 'right'

                                }
                            }
                else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'right' || dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'left'){
                            options['legend'] = {
                                     data: dataset.name,
                                    left: 'right'
                                }
                            }
                else if (dict_data.legend_position == 'bottom' || dict_data.legend_horizontal_align == 'right' || dict_data.legend_horizontal_align == 'right'){
                            options['legend'] = {
                                     data: dataset.name,
                                    bottom: 'left'

                                }
                            }
                else{
                options['legend'] = {
                                     data: dataset.name,
                                    top :'bottom'

                                }
                }
            options['tooltip'] = {
                        trigger: 'axis'

                    },
			options['xAxis'] = {

					type: 'category',
//                    boundaryGap: false,
    				data: dataset.model_label_list,
				},
			options['yAxis'] = {

					type: 'value',

				},
			options['series'] = dataset.data_list


            }

            if (dict_data.chart_type == 'line'){
                options['tooltip'] = {
					trigger: 'axis'

				},
			options['legend'] = {
					 data: dataset.name,
					top: 'bottom'
				},
			options['xAxis'] = {
					type: 'category',
//                    boundaryGap: false,
    				data: dataset.model_label_list,
				},
			options['yAxis'] = {
					type: 'value',

				},
			options['series'] =dataset.data_list
            }

             self.$(".grid-stack").on('gsresizestop', function(event, elem) {
                myChart.resize();
            });
            myChart.resize();
            options && myChart.setOption(options);


            var update_button_container = $(QWeb.render('ChartUpdateButton', {
                'id': dict_data.id,
            }));
            var new_chart = self.$(".grid-stack").find(`[id='chart_item_${dashboard_item_id}']`)
            var new_grid_item = self.$(".grid-stack").find(`[id='chart_item_${dashboard_item_id}']`).find('.grid-stack-item-content')
            new_grid_item.prepend(update_button_container);
            },

        chart_legend_option: function(dict_data){
                var self = this;
                var legend;
                if (dict_data.is_show_legend){
                    legend = {
                        show: true,
                        position: dict_data.legend_position,
                        horizontalAlign: dict_data.legend_horizontal_align,
                    }
                }
                else{
                    legend = {
                        show: false,
                    }
                }
                return legend;
            },

        destroy: function () {
            this._super.apply(this, arguments);
        },

    });

    core.action_registry.add('custom_dashboard_client_action', CustomDashboardBoard);
    return {
        CustomDashboardBoard:  CustomDashboardBoard,
    };

});