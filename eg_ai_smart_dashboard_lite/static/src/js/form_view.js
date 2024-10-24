/** @odoo-module */

import {registry} from '@web/core/registry';
import {formView} from '@web/views/form/form_view';
import {FormController} from '@web/views/form/form_controller';
import {FormRenderer} from '@web/views/form/form_renderer';
import { qweb as QWeb } from 'web.core';
import {Component,onWillStart,onMounted,useEffect,useRef,onRendered,useState,toRaw} from "@odoo/owl";
import ajax from 'web.ajax';
import { buildQuery } from "web.rpc";
import { useService } from "@web/core/utils/hooks";


export class DashboardItemFormController extends FormController {
	setup() {
		super.setup();
		this.rpc = useService('rpc');
		onRendered(() => {
			this._render_chart();
		});
		onMounted(() => {
			this._render_chart();
		});
	}

	_render_chart() {
		var self = this;
		var options = {};
		if (this.model.root.data.id){
		    var item_id =this.model.root.data.id
		}
		else{
		    var item_id =self.props.resId
		}
		var chartDom = $('#custom-chart-preview');
		$('#custom-chart-preview').removeClass('tile-kpi-view');

		if(chartDom[0] && echarts.getInstanceByDom(chartDom[0])){
		    echarts.getInstanceByDom(chartDom[0]).dispose()
		 }

        if (item_id){
//            $("#plate-color").spectrum({
//					color: "#fff"
//				});
//				$("#background-Color").spectrum({
//					color: "#fff"
//				});
//				$("#grid-color").spectrum({
//					color: "#fff"
//				});
				 if (['kpi','tiles'].includes(this.model.root.data.chart_type)){
                        self.generate_kpi_or_tiles(this.model.root.data, item_id, chartDom)
                    }else if (this.model.root.data.chart_type == 'list') {
					self.generate_list_view(this.model.root.data,item_id, chartDom)
				} else {
					self._getChartData(this.model.root.data, item_id, chartDom);
				}

//            ajax.jsonRpc("/custom_dashboard/get_dashboard_items_data", 'call', {
//				'dashboard_item_id': item_id,
//				'data':this.model.root.data
//			})
//			.then(function(res) {
//
//			});
        }



	}

	async generate_kpi_or_tiles(dict_data, dashboard_item_id, chartDom){
	    var self = this;

		$('#custom-chart-preview').addClass('tile-kpi-view');
        if(chartDom[0]){
		    chartDom[0].innerHTML = "";
		}
		if (!dict_data.chart_data){
            const rpcQuery = buildQuery({
                model: 'eg.custom.dashboard.item',
                method: 'compute_chart_chart',
                args: [dashboard_item_id],
            })
            const result = await this.rpc(rpcQuery.route, rpcQuery.params);
            dict_data.chart_data=result
		}
        var dataset = JSON.parse(dict_data.chart_data)
        var render_data={
            'layout':dict_data.tile_kpi_layout,
            'icon_bgcolor':dict_data.icon_bgcolor,
            'icon_color':dict_data.icon_color,
            'tile_kpi_theme':dict_data.tile_kpi_theme,
//            'title_font': dict_data.title_font,
            'background_color':dict_data.chart_background_color,
            'text_color': dict_data.chart_fore_color,
            'tile_image_type': dict_data.tile_image_type,
            'tile_icon': dict_data.tile_icon,
            'title':  dict_data.name,
//            'image_url': image_src,
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
        }
//        var $chartContainer = $(QWeb.render(template_id, render_data));
//        this.$el.append(qweb.render('accountTypeSelection', {widget: this}));
        chartDom.append(QWeb.render(template_id, render_data));
	}

	_getChartData(dict_data, dashboard_item_id, chartDom) {
		if ($.find('#custom-chart-preview').length > 0) {
			this.generate_chart_options(dict_data, dashboard_item_id, chartDom);
		}
	}
	async generate_chart_options(dict_data, dashboard_item_id, chartDom) {
		var fields = dict_data
		if (!dict_data.chart_data){
            const rpcQuery = buildQuery({
                model: 'eg.custom.dashboard.item',
                method: 'compute_chart_chart',
                args: [dashboard_item_id],
            })
            const result = await this.rpc(rpcQuery.route, rpcQuery.params);
            dict_data.chart_data=result
		}
		var dataset = JSON.parse(fields.chart_data)

		if (fields.chart_theme) {
			var myChart = echarts.init(chartDom[0], fields.chart_theme);
		} else {
			var myChart = echarts.init(chartDom[0]);
		}
//		myChart.on('mouseover', {item_id: dashboard_item_id}, function (params) {
//            console.log(params);
//        });

		var optionechart = {
			toolbox: {
				show: fields.tool_box_show,
				feature: {
					dataZoom: {
						yAxisIndex: "none"
					},
					dataView: {
						readOnly: false
					},
					magicType: {
						type: ["line", "bar"]
					},
					restore: {},
					saveAsImage: {}
				}
			},
			backgroundColor: dict_data.chart_background_color,
			title: {
				text: fields.name,
				subtext: fields.sub_text,
				left: fields.name_align_position,
				textStyle: {
					fontSize: 30,
				},
				subtextStyle: {
					color: fields.font_color,
					fontFamily: fields.font_family,
					fontFamily: fields.sub_title_size,

				},
				textAlign: fields.text_aline,
				show: true,
				backgroundColor: fields.chart_title_background_color,

			},
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
			xAxis: {
				show: fields.is_enable_x_axis,
			},
			yAxis: {
				show: fields.is_enable_y_axis,
			},
			animationType: 'scale',
            animationEasing: dict_data.animation_easing_type,
            animationDuration:dict_data.animation_speed,
			 animationDelay: function (idx) {
                return Math.random() * dict_data.animation_gradually_delay;
             }


		};

		if (dict_data.chart_type == 'bar') {
		    if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'left'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                left: 'top'

                            }
                        }

            else if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'right'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                right: 'top'

                            }
                        }
            else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'left'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                left: 'left'

                            }
                        }
            else if (dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'right'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                right: 'right'

                            }
                        }
            else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'right' || dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'left'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                left: 'right'
                            }
                        }
            else if (dict_data.legend_position == 'bottom' || dict_data.legend_horizontal_align == 'right' || dict_data.legend_horizontal_align == 'right'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                bottom: 'left'

                            }
                        }
            else{
            optionechart['legend'] = {
                                 data: dataset.name,
                                top :'bottom'

                            }
            }
        optionechart['tooltip'] = {
					trigger: 'axis'

				}
			optionechart['xAxis'] = {
					type: 'value',
				},
			optionechart['yAxis'] = {

					type: 'category',
//                    boundaryGap: false,
    				data: dataset.model_label_list,

				},
			optionechart['series'] = dataset.data_list


		}

		if (dict_data.chart_type == 'column') {
          if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'left'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                left: 'top'

                            }
                        }

            else if (dict_data.legend_position == 'top' && dict_data.legend_horizontal_align == 'right'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                right: 'top'

                            }
                        }
            else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'left'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                left: 'left'

                            }
                        }
            else if (dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'right'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                right: 'right'

                            }
                        }
            else if (dict_data.legend_position == 'left' && dict_data.legend_horizontal_align == 'right' || dict_data.legend_position == 'right' && dict_data.legend_horizontal_align == 'left'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                left: 'right'
                            }
                        }
            else if (dict_data.legend_position == 'bottom' || dict_data.legend_horizontal_align == 'right' || dict_data.legend_horizontal_align == 'right'){
                        optionechart['legend'] = {
                                 data: dataset.name,
                                bottom: 'left'

                            }
                        }
            else{
            optionechart['legend'] = {
                                 data: dataset.name,
                                top :'bottom'

                            }
            }


			optionechart['tooltip'] = {
					trigger: 'axis'

				},
			optionechart['xAxis'] = {

					type: 'category',
//                    boundaryGap: false,
    				data: dataset.model_label_list,
				},
			optionechart['yAxis'] = {

					type: 'value',

				},
			optionechart['series'] = dataset.data_list


		}

		if (dict_data.chart_type == 'line') {
             optionechart['tooltip'] = {
					trigger: 'axis'

				},
			optionechart['legend'] = {
					 data: dataset.name,
					top: 'bottom'
				},
			optionechart['xAxis'] = {
					type: 'category',
//                    boundaryGap: false,
    				data: dataset.model_label_list,
				},
			optionechart['yAxis'] = {
					type: 'value',

				},
			optionechart['series'] =dataset.data_list
		}






		optionechart && myChart.setOption(optionechart);

	}


}

//// TODO KBA: to remove in master
//export class EmployeeFormRenderer extends FormRenderer {
//    setup() {
//        super.setup();
//
//    }
//
//}

registry.category('views').add('eg_custom_dashboard_item_form_view', {
	...formView,
	Controller: DashboardItemFormController,
	//    Renderer: EmployeeFormRenderer,
});