import json

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import date_utils
from odoo.exceptions import UserError


class EgCustomDashboardItem(models.Model):
    _name = 'eg.custom.dashboard.item'
    _description = 'Eg Custom Dashboard Item'

    def open_barcode_item_form_view(self):
        """
        Inventory adjustment kanban view through any inventory open when show a custom barcode inventory adjustment view shows
        :return: action of barcode inventory adjustment
        """
        action = self.env.ref('eg_ai_smart_dashboard_lite_lite.dashboard_item_view_action').read()[0]
        params = {
            'model': 'eg.custom.dashboard.item',
            'dashboard_item_view_id': self.id,
        }
        return dict(action, target='new', params=params)

    @api.model
    def default_get(self, fields):
        res = super(EgCustomDashboardItem, self).default_get(fields)
        if 'chart_color' in fields:
            res['chart_color'] = True
        return res

    name = fields.Char(string='Name')
    chart_type = fields.Selection(
        [('bar', 'Bar Chart'), ('pie', 'Pie Chart'), ('column', 'Column Chart'),
         ('line', 'Line Chart'), ('area', 'Area Chart'), ('treemap', 'Treemap'), ('radar', 'Radar Chart'),
         ('polarArea', 'Polar Area'), ('funnel', 'Funnel Chart'),
         ('tiles', 'Tiles'), ('list', 'List'), ('kpi', 'KPI')],
        default=lambda self: self._context.get('chart_type'),
        required=True)
    custom_dashboard_board_id = fields.Many2one(comodel_name='custom.dashboard.board',
                                                default=lambda self: self._context.get('custom_dashboard_board_id'))
    # odoo fields, models
    ir_model_id = fields.Many2one(comodel_name='ir.model', string='Model Name')
    model_name = fields.Char(string="Model Name")
    measure_model_field_ids = fields.Many2many(comodel_name='ir.model.fields',
                                               domain="[('model_id','=',ir_model_id),('name','!=','id'),('store','=',True),'|','|',('ttype','=','integer'),('ttype','=','float'),('ttype','=','monetary')]")
    label_model_field_id = fields.Many2one(comodel_name='ir.model.fields',
                                           domain="[('model_id','=',ir_model_id), ('name','!=','id'), ('store','=',True),('ttype','!=','boolean'), ('ttype','!=','binary'), ('ttype','!=','many2many'), ('ttype','!=','one2many')]")
    list_view_field_ids = fields.Many2many(comodel_name='ir.model.fields', relation='list_view_fields_rel',
                                           domain="[('model_id','=',ir_model_id), ('name','!=','id'), ('store','=',True),('ttype','!=','boolean'), ('ttype','!=','binary'), ('ttype','!=','many2many'), ('ttype','!=','one2many')]")
    is_group_by_data = fields.Boolean(string='Groupby Data')
    group_by_measure_field_id = fields.Many2one(comodel_name='ir.model.fields',
                                                domain="[('model_id','=',ir_model_id), ('name','!=','id'), ('store','=',True),('ttype','!=','boolean'), ('ttype','!=','binary'), ('ttype','!=','many2many'), ('ttype','!=','one2many')]",
                                                string='Group By Field')
    group_by_measure_field_type = fields.Char(string='Measure Field Name',
                                              compute='_compute_group_by_measure_field_type')
    group_by_filter = fields.Selection(string='Group Filter',
                                       selection=[('day', 'Day'), ('week', 'Week'), ('month', 'Month'),
                                                  ('quarter', 'Quarter'), ('year', 'Year')])
    record_limit = fields.Integer(string='Record Limit')
    record_sort_field = fields.Many2one(comodel_name='ir.model.fields',
                                        domain="[('model_id','=',ir_model_id),('name','!=','id'),('ttype','!=','binary'),('store','=',True),('ttype','!=','one2many')]")
    record_sort = fields.Selection([('ASC', 'Ascending'), ('DESC', 'Descending')], default='ASC', string='Record Sort')
    filter_domain = fields.Char(string="Domain")
    # KPI
    kpi_model_id = fields.Many2one(comodel_name='ir.model', string='Model Name')
    kpi_model_name = fields.Char(string="Model Name")
    kpi_calculation_type = fields.Selection([('count', 'Count'), ('sum', 'Sum')], default='sum',
                                            string='KPi Calculation Type')
    kpi_measure_field_id = fields.Many2one(comodel_name='ir.model.fields',
                                           domain="[('model_id','=',kpi_model_id),('name','!=','id'),('store','=',True),'|','|',('ttype','=','integer'),('ttype','=','float'),('ttype','=','monetary')]",
                                           string='Measure Field')
    kpi_data_calculation_type = fields.Selection(
        [('none', 'None'), ('sum', 'Sum'), ('ratio', 'Ratio'), ('percentage', 'Percentage')],
        string='Data Calculation Type', default='none')
    kpi_filter_domain = fields.Char(string='Domain')
    kpi_date_filter_field_id = fields.Many2one(comodel_name='ir.model.fields', string='Date Filter Field',
                                               domain="[('model_id','=',kpi_model_id), '|',('ttype','=','datetime'),('ttype','=','date')]")
    kpi_date_record_filter_type = fields.Selection(
        [('none', 'None'), ('today', 'Today'), ('this_week', 'This Week'), ('this_month', 'This Month'),
         ('last_month', 'Last Month'),
         ('last_week', 'Last Week'), ('this_year', 'This Year'), ('last_year', 'Last Year'),
         ('last_90_days', 'Last 90 Days'), ('last_15_days', 'Last 15 days'), ('custom_filter', 'Custom Filter')],
        default='none', string='Date Filter Type')
    kpi_start_date = fields.Datetime('Start Date')
    kpi_end_date = fields.Datetime('End Date')
    kpi_record_amount = fields.Float(string='Record Amount')
    # odoo date filter
    date_record_filter_type = fields.Selection(
        [('none', 'None'), ('today', 'Today'), ('this_week', 'This Week'), ('this_month', 'This Month'),
         ('last_month', 'Last Month'),
         ('last_week', 'Last Week'), ('this_year', 'This Year'), ('last_year', 'Last Year'),
         ('last_90_days', 'Last 90 Days'), ('last_15_days', 'Last 15 days'), ('custom_filter', 'Custom Filter')],
        default='none')
    date_filter_field = fields.Many2one(comodel_name='ir.model.fields', string='Date Filter Field',
                                        domain="[('model_id','=',ir_model_id), '|',('ttype','=','datetime'),('ttype','=','date')]")
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    # chart configuration
    name_align_position = fields.Selection([('left', 'Left'), ('center', 'Center'), ('right', 'Right')],
                                           default='center')
    chart_theme = fields.Selection(
        [('light', 'Light'), ('dark', 'Dark'), ('custom', 'Custom'), ('infographic', 'Infographic'), ('shine', 'Shine'),
         ('roma', 'Roma'),
         ('macarons', 'Macarons'), ('vintage', 'Vintage'), ('westeros', 'Westeros'),
         ('purple-passion', 'Purple-passion'), ('walden', 'Walden'),
         ('essos', 'Essos'), ('halloween', 'Halloween'), ('chalk', 'Chalk'), ('wonderland', 'wonderland'),
         ('customed', 'Customed'), ('green', 'Green'), ('azul', 'Azul'),
         ('bee-inspired', 'Bee-Inspired'), ('blue', 'Blue'), ('caravan', 'Caravan'), ('carp', 'Carp'), ('cool', 'Cool'),
         ('dark-blue', 'Dark-Blue'),
         ('dark-bold', 'Dark-Bold'), ('dark-digerati', 'Dark-Digerati'), ('dark-fresh-cut', 'Dark-Fresh-cut'),
         ('dark-mushroom', 'Dark-Mushroom'),
         ('eduardo', 'Eduardo'), ('forest', 'Forest'), ('fresh-cut', 'Fresh-Cut'), ('fruit', 'Fruit'), ('gray', 'Gray'),
         ('helianthus', 'Helianthus'),
         ('inspired', 'Inspired'), ('jazz', 'Jazz'), ('london', 'London'), ('mint', 'Mint'), ('red', 'Red'),
         ('red-velvet', 'Red-Velvet'), ('royal', 'Royal'),
         ('sakura', 'Sakura'), ('tech-blue', 'Tech-Blue')],
        string='Chart Theme', default='light')
    color_palette_echars = fields.Char(string='Plate Colour', default='#fff')
    color_palette = fields.Selection(
        [('palette1', 'Palette-1'), ('palette2', 'Palette-2'), ('palette3', 'Palette-3'), ('palette4', 'Palette-4'),
         ('palette5', 'Palette-5'), ('palette6', 'Palette-6'), ('palette7', 'Palette-7'), ('palette8', 'Palette-8'),
         ('palette9', 'Palette-9'), ('palette10', 'Palette-10')], default='palette1', string='Color Palette')
    # Chart Grid Configurations
    is_show_grid = fields.Boolean(string='Enable Show Grid', default=False)
    grid_position = fields.Selection([('front', 'Front'), ('back', 'Back')], string='Grid Position', default='back')
    grid_color = fields.Char(string="Grid Color", default='#ffffff')
    grid_bg_color = fields.Char(string="Grid BackGround Color", default='#ffffff')
    grid_border_width = fields.Char(string="Border Width")
    grid_shadow_color = fields.Char(string="Shadow Color", default='#ffffff')
    grid_shadow_blur = fields.Char(string="Shadow blur")

    stork_dash_array = fields.Float(string='Space between dashes', default=0)
    is_enable_x_axis = fields.Boolean(string='Enable show X Axis')
    is_enable_y_axis = fields.Boolean(string='Enable show Y Axis')
    # stork type for Line Chart
    stork_type = fields.Selection([('smooth', 'Smooth'), ('straight', 'Straight'), ('stepline', 'Stepline')],
                                  string='Stork Line Type', default='straight')
    is_show_datalabels = fields.Boolean(string='Enable show Datalabels')
    datalabels_unit = fields.Char(string='Datalabels Unit')
    is_treemap_distributed = fields.Boolean(string='Treemap Distributed')

    tile_image_type = fields.Selection([('default_icons', 'Default Icons')],
                                       default='default_icons')
    tile_image_selection = fields.Binary(string='Custom Icon or Image')
    tile_icon = fields.Char(string='Tile Icon')
    tile_unit = fields.Char(string='Tile Unit')
    tile_record_amount = fields.Float('Record Amount')
    calculation_type = fields.Selection([('count', 'Count'), ('sum', 'Sum')], default='sum', string="Calculation ")
    graph_preview = fields.Char(string='Graph Preview')
    chart_data = fields.Char(string='Chart data', compute='compute_chart_chart')
    # Chart Legend
    is_check_show_legend = fields.Boolean(string='Is Check show Legend Field', compute='_compute_is_check_show_legend')
    is_show_legend = fields.Boolean(string='Enable show Legend')
    legend_position = fields.Selection([('top', 'Top'), ('right', 'Right'), ('bottom', 'Bottom'), ('left', 'Left')],
                                       string='Legend Position')
    legend_horizontal_align = fields.Selection([('left', 'Left'), ('right', 'Right')],
                                               string='Legend Horizontal Align')

    is_chart_zoom = fields.Boolean(string='Enable Chart Zoom')
    is_stack_chart = fields.Boolean(string='Stack Chart')

    is_distributed_chart = fields.Boolean(string='Distributed Chart')
    is_reserved_chart = fields.Boolean(string='Reverse Chart')
    # Chart style
    chart_background_color = fields.Char(string='Background Color', default="#FFFFFF")
    chart_fore_color = fields.Char(string='Text Color', default="#373d3f")
    icon_bgcolor = fields.Char(string='Icon Background Color', default="#000000")
    icon_color = fields.Char(string='Icon Color', default="#ffffff")

    pattern_type = fields.Selection(
        [('verticalLines', 'Vertical Lines'), ('horizontalLines', 'Horizontal'),
         ('slantedLines', 'Slanted Lines'), ('squares', 'Squares'), ('circles', 'Circles')], default='verticalLines')
    # Chart Animation
    is_enable_animation = fields.Boolean(string='Enable Animation', default=False)
    animation_easing_type = fields.Selection(
        [('linear', 'Linear'), ('backIn', 'Back In'), ('backOut', 'Back Out'), ('backInOut', 'BackInOut'),
         ('bounceIn', 'Bounce In'), ('bounceOut', 'Bounce Out'), ('bounceInOut', 'bounceInOut')],
        default='linear')
    animation_speed = fields.Integer(string="Animation Speed", default=800)
    is_enable_animation_gradually = fields.Boolean(string='Gradually animate one by one')
    animation_gradually_delay = fields.Integer(string='Animation Gradually Delay', default=150)
    # dashboard position use for items gridstack positions
    chart_dashboard_positions = fields.Char(string='chart Dashboard Position')
    nightingale_chart = fields.Boolean(default=True)
    access_from_chart = fields.Boolean()
    simple_chart = fields.Boolean()
    tile_kpi_layout = fields.Selection([('layout1', 'Layout 1'),
                                        ('layout2', 'Layout 2'),
                                        ('layout3', 'Layout 3'),
                                        ('layout4', 'Layout 4'),
                                        ('layout5', 'Layout 5'),
                                        ], default=('layout1'), required=True, string="Layout",
                                       help=' Select the layout to display records. ')

    tile_kpi_theme = fields.Integer(string="Color")
    title_font = fields.Char(string="Title Font Size")

    def unlink(self):
        print(123)
        return super(EgCustomDashboardItem, self).unlink()

    @api.onchange('is_show_grid', 'is_enable_animation')
    def _onchange_grid_and_animation(self):
        if self.is_enable_animation:
            raise UserError(
                _('Free/Lite version not supports Animation Feature. Upgrade to full version to user Animation Features.\n https://www.inkerp.com/odoo_dashboard'))
        if self.is_show_grid:
            raise UserError(
                _('Free/Lite version not supports Grid Feature. Upgrade to full version to user Grid Features.\n https://www.inkerp.com/odoo_dashboard'))

    @api.onchange('tile_kpi_theme', 'tile_kpi_layout')
    def _onchange_tile_kpi_theme(self):
        if self.chart_type == 'kpi':
            if self.tile_kpi_theme == 0:
                self.chart_background_color = '#FFFFFF'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#4e73df'
            elif self.tile_kpi_theme == 1:
                self.chart_background_color = '#F06050'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#F06050'
                self.icon_bgcolor = '#F06050' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 2:
                self.chart_background_color = '#F4A460'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#F4A460'
                self.icon_bgcolor = '#F4A460' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 3:
                self.chart_background_color = '#f7cb3d'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#f7cb3d'
                self.icon_bgcolor = '#f7cb3d' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 4:
                self.chart_background_color = '#6dc2eb'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#6dc2eb'
                self.icon_bgcolor = '#6dc2eb' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 5:
                self.chart_background_color = '#804a67'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#804a67'
                self.icon_bgcolor = '#804a67' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 6:
                self.chart_background_color = '#ff9093'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#ff9093'
                self.icon_bgcolor = '#ff9093' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 7:
                self.chart_background_color = '#2e8496'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#2e8496'
                self.icon_bgcolor = '#2e8496' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 8:
                self.chart_background_color = '#475676'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#475676'
                self.icon_bgcolor = '#475676' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 9:
                self.chart_background_color = '#d5145e'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#d5145e'
                self.icon_bgcolor = '#d5145e' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 10:
                self.chart_background_color = '#37c285'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#37c285'
                self.icon_bgcolor = '#37c285' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'
            elif self.tile_kpi_theme == 11:
                self.chart_background_color = '#9267b5'
                self.icon_color = '#fff' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#9267b5'
                self.icon_bgcolor = '#9267b5' if self.tile_kpi_layout in ['layout1', 'layout5'] else '#fff'

    @api.onchange('chart_theme')
    def _onchange_chart_theme(self):
        if self.chart_theme in ['light', 'dark', 'custom', False]:
            if self.chart_theme:
                self.chart_background_color = '#FFFFFF'
            if self.chart_theme == 'dark':
                self.chart_background_color = 'black'
        else:
            raise UserError(
                _('Free/Lite version only supports Custom, Lite, Dark and Dark-Blue Theme. Upgrade to full version to user all Theme.\n https://www.inkerp.com/odoo_dashboard'))

    @api.depends('group_by_measure_field_id')
    def _compute_group_by_measure_field_type(self):
        for rec in self:
            if rec.group_by_measure_field_id:
                rec.group_by_measure_field_type = rec.group_by_measure_field_id.ttype
            else:
                rec.group_by_measure_field_type = False

    @api.model
    def create(self, vals_list):
        res = super(EgCustomDashboardItem, self).create(vals_list)
        return res

    @api.depends('measure_model_field_ids', 'is_distributed_chart', 'chart_type')
    def _compute_is_check_show_legend(self):
        for rec in self:
            if (len(rec.measure_model_field_ids.ids) > 1 and rec.chart_type not in [
                'tiles']) or rec.is_distributed_chart:
                rec.is_check_show_legend = True
            else:
                rec.is_check_show_legend = False

    @api.onchange('calculation_type')
    def _onchange_calculation_type(self):
        if self.calculation_type == 'count':
            self.measure_model_field_ids = False

    @api.onchange('ir_model_id')
    def _onchange_ir_model_id(self):
        if self.ir_model_id:
            self.label_model_field_id = False
            self.measure_model_field_ids = False
            self.filter_domain = False
            self.model_name = self.ir_model_id.model
            create_field_id = self.env['ir.model.fields'].search(
                [('name', '=', 'create_date'), ('model_id', '=', self.ir_model_id.id)])
            self.date_filter_field = create_field_id.id

    @api.onchange('chart_type')
    def _onchange_chart_type(self):
        if self.chart_type:
            self.label_model_field_id = False
            self.measure_model_field_ids = False
            self.is_group_by_data = False
            if self.chart_type == 'tiles':
                self.chart_background_color = '#ffff'
                self.chart_fore_color = '#fff'
                self.tile_image_type = 'default_icons'
                self.tile_icon = 'fa-line-chart'
                self.is_group_by_data = False
            elif self.chart_type == 'bar':
                self.is_enable_x_axis = True
                self.is_enable_y_axis = False
            elif self.chart_type == 'column':
                self.is_enable_y_axis = True
                self.is_enable_x_axis = False
            elif self.chart_type == 'line':
                self.is_chart_zoom = True
                self.is_enable_y_axis = True
                self.is_enable_x_axis = False

    @api.onchange('is_show_legend')
    def _onchange_is_show_legend(self):
        if not self.is_show_legend:
            self.legend_position = False
            self.legend_horizontal_align = False
        else:
            self.legend_position = 'top'
            self.legend_horizontal_align = 'left'

    @api.onchange('is_show_datalabels')
    def _onchange_is_show_datalabels(self):
        if not self.is_show_datalabels:
            self.datalabels_unit = False

    @api.depends('ir_model_id', 'label_model_field_id', 'date_record_filter_type', 'date_filter_field',
                 'is_group_by_data', 'group_by_measure_field_id', 'group_by_filter',
                 'measure_model_field_ids', 'record_sort_field', 'record_sort', 'list_view_field_ids', 'record_limit',
                 'filter_domain', 'start_date', 'end_date',
                 'chart_type')
    def compute_chart_chart(self):
        global label
        for rec in self:
            if rec.chart_type not in ['bar', 'column', 'line', 'tiles', False]:
                raise UserError(
                    _('Free/Lite version only supports Line, Column, Bar and Tile Chart. Upgrade to full version to user all Chart.\n https://www.inkerp.com/odoo_dashboard'))
            else:
                if rec.ir_model_id:
                    search_domain = rec.filter_record(rec.date_record_filter_type, rec.date_filter_field,
                                                      rec.filter_domain,
                                                      rec.start_date, rec.end_date)
                    if not rec.record_sort_field:
                        model_data_ids = self.env[rec.ir_model_id.model].search(search_domain,
                                                                                limit=rec.record_limit)
                    else:
                        model_data_ids = self.env[rec.ir_model_id.model].search(search_domain,
                                                                                order='{} {}'.format(
                                                                                    rec.record_sort_field.name,
                                                                                    rec.record_sort),
                                                                                limit=rec.record_limit)

                    if rec.ir_model_id and rec.measure_model_field_ids and (
                            rec.label_model_field_id or rec.group_by_measure_field_id):
                        if rec.chart_type in ['bar', 'column', 'line']:
                            if rec.is_group_by_data and rec.group_by_measure_field_id:
                                rec.chart_data = rec._is_group_by_data_generate(search_domain)
                            else:
                                measure_data_list = []
                                max_data = []
                                name_label = []
                                stack_value = None
                                for measure_model_field_id in rec.measure_model_field_ids:
                                    data_list = []
                                    funnel_data_list = []
                                    model_label_list = []
                                    for model_data_id in model_data_ids:
                                        data_list.append(model_data_id[measure_model_field_id.name])
                                        if rec.label_model_field_id.ttype == 'datetime':
                                            date_time = model_data_id[rec.label_model_field_id.name].strftime(
                                                DEFAULT_SERVER_DATETIME_FORMAT)
                                            model_label_list.append(date_time)
                                        elif rec.label_model_field_id.ttype == 'date':
                                            date_time = model_data_id[rec.label_model_field_id.name].strftime(
                                                DEFAULT_SERVER_DATE_FORMAT)
                                            model_label_list.append(date_time)
                                        elif rec.label_model_field_id.ttype == 'many2one':
                                            name = model_data_id[rec.label_model_field_id.name].name
                                            model_label_list.append(name)
                                        else:
                                            label = model_data_id[rec.label_model_field_id.name]
                                            max_data.append(max(data_list))
                                            model_label_list.append(model_data_id[rec.label_model_field_id.name])
                                    if rec.chart_type in ['line', 'bar', 'column']:
                                        if rec.chart_type == 'column':
                                            if not stack_value:
                                                stack_value = measure_model_field_id.field_description,
                                            data_dict = {
                                                'type': 'bar',
                                                'label': {'show': True if self.is_show_datalabels else False},
                                                'stack': stack_value if self.is_stack_chart else False,
                                                'emphasis': {
                                                    'focus': 'series'
                                                },
                                                'name': measure_model_field_id.field_description,
                                                'data': data_list
                                            }

                                        elif rec.chart_type == 'bar':
                                            if not stack_value:
                                                stack_value = measure_model_field_id.field_description,
                                            data_dict = {
                                                'type': rec.chart_type,
                                                'label': {'show': True if self.is_show_datalabels else False},
                                                'stack': stack_value if self.is_stack_chart else False,
                                                'emphasis': {
                                                    'focus': 'series'
                                                },
                                                'name': measure_model_field_id.field_description,
                                                'data': data_list
                                            }
                                        else:
                                            data_dict = {
                                                'type': rec.chart_type,
                                                'name': measure_model_field_id.field_description,
                                                'data': data_list
                                            }
                                        name_label.append(measure_model_field_id.field_description)
                                        measure_data_list.append(data_dict)

                                return_dict = {
                                    'name': name_label,
                                    'data_list': measure_data_list,
                                    'model_label_list': model_label_list,
                                    'max': max(max_data if max_data else [0])
                                }
                                rec.chart_data = json.dumps(return_dict)

                    elif rec.ir_model_id and rec.chart_type == 'tiles':
                        if rec.calculation_type == 'sum' and rec.measure_model_field_ids:
                            total = 0
                            for model_data_id in model_data_ids:
                                total += model_data_id[rec.measure_model_field_ids[0].name]
                            return_dict = {
                                'total': format(total, '.2f')
                            }
                            rec.chart_data = json.dumps(return_dict)
                        elif rec.calculation_type == 'count':
                            record_count = len(model_data_ids.ids)
                            return_dict = {
                                'total': record_count,
                            }
                            rec.chart_data = json.dumps(return_dict)
                        else:
                            return_dict = {
                                'total': 0,
                            }
                            rec.chart_data = json.dumps(return_dict)
                    else:
                        rec.chart_data = False

                else:
                    rec.chart_data = False

        return self[0].chart_data

    def filter_record(self, date_record_filter_type=None, date_filter_field=None, filter_domain=None, start_date=None,
                      end_date=None):
        if date_record_filter_type in ['none']:
            date_filter_list = []
            if filter_domain:
                if len(eval(filter_domain)) > 1:
                    for domain_list in eval(filter_domain)[1:]:
                        date_filter_list.append(tuple(domain_list))
                else:
                    for domain_list in eval(self.filter_domain):
                        date_filter_list.append(tuple(domain_list))
            return date_filter_list
        else:
            if date_filter_field.ttype == 'date':
                field_type = fields.Date.context_today(self)
            else:
                field_type = fields.Datetime.now()

            date_filter_list = []
            if date_record_filter_type == 'today':
                date_filter_list.append((date_filter_field.name, '>=', date_utils.start_of(field_type, 'day')))
                date_filter_list.append((date_filter_field.name, '<=', date_utils.end_of(field_type, 'day')))
            elif date_record_filter_type == 'this_week':
                date_filter_list.append((date_filter_field.name, '>=', date_utils.start_of(field_type, 'week')))
                date_filter_list.append((date_filter_field.name, '<=', date_utils.end_of(field_type, 'week')))
            elif date_record_filter_type == 'this_week':
                date_filter_list.append((date_filter_field.name, '>=', date_utils.start_of(field_type, 'month')))
                date_filter_list.append((date_filter_field.name, '<=', date_utils.end_of(field_type, 'month')))
            else:
                raise UserError(
                    _('Free/Lite version only supports Today, This Week and This Week Filters. Upgrade to full version to user all Filters.\n https://www.inkerp.com/odoo_dashboard'))

            if filter_domain:
                if len(eval(filter_domain)) > 1:
                    for domain_list in eval(filter_domain)[1:]:
                        date_filter_list.append(tuple(domain_list))
                else:
                    for domain_list in eval(filter_domain):
                        date_filter_list.append(tuple(domain_list))
            return date_filter_list

    def calculate_aspect(self, width, height):
        def gcd(a, b):
            """The GCD (greatest common divisor) is the highest number that evenly divides both width and height."""
            return a if b == 0 else gcd(b, a % b)

        r = gcd(width, height)
        x = int(width / r)
        y = int(height / r)

        return f"{x}:{y}"

    def _is_group_by_data_generate(self, search_domain):
        measure_data_list = []
        new_measure_data_list = []
        max_data = []
        model_label_list = []
        measure_and_label_list = []
        treemap_data_list = []
        stack_value = None
        if self.group_by_measure_field_id:
            if self.group_by_measure_field_id.ttype not in ['datetime', 'date']:
                if self.group_by_measure_field_id.ttype in ['many2one']:
                    if self.record_sort_field and self.record_sort:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            self.group_by_measure_field_id.name], domain=search_domain, limit=self.record_limit,
                                                                                     orderby='{} {}'.format(
                                                                                         self.record_sort_field.name,
                                                                                         self.record_sort))
                    else:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            self.group_by_measure_field_id.name], domain=search_domain, limit=self.record_limit)
                    for model_data_id in model_data_ids:
                        treemap_dict = {}
                        pie_dict = {}

                        if self.calculation_type == 'sum':
                            measure_data_list.append(model_data_id.get(self.measure_model_field_ids[0].name))
                            treemap_dict.update({'value': model_data_id.get(self.measure_model_field_ids[0].name)})
                            pie_dict.update({'value': model_data_id.get(self.measure_model_field_ids[0].name)})

                        else:
                            measure_data_list.append(
                                model_data_id.get("{}_count".format(self.group_by_measure_field_id.name)))
                            treemap_dict.update(
                                {'value': model_data_id.get("{}_count".format(self.group_by_measure_field_id.name))})
                            pie_dict.update(
                                {'value': model_data_id.get("{}_count".format(self.group_by_measure_field_id.name))})
                        max_data.append(max(measure_data_list))
                        label = model_data_id.get(self.group_by_measure_field_id[0].name) if not model_data_id.get(
                            self.group_by_measure_field_id[0].name) else \
                            model_data_id.get(self.group_by_measure_field_id[0].name)[1]

                        model_label_list.append(
                            model_data_id.get(self.group_by_measure_field_id[0].name) if not model_data_id.get(
                                self.group_by_measure_field_id[0].name) else
                            model_data_id.get(self.group_by_measure_field_id[0].name)[1])
                        treemap_dict.update(
                            {'name': model_data_id.get(self.group_by_measure_field_id[0].name) if not model_data_id.get(
                                self.group_by_measure_field_id[0].name) else
                            model_data_id.get(self.group_by_measure_field_id[0].name)[1]})
                        pie_dict.update({'name': model_data_id.get(self.group_by_measure_field_id.name)})

                        treemap_data_list.append(treemap_dict)
                        measure_and_label_list.append(pie_dict)
                else:
                    if self.record_sort_field and self.record_sort:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            self.group_by_measure_field_id.name], domain=search_domain, limit=self.record_limit,
                                                                                     orderby='{} {}'.format(
                                                                                         self.record_sort_field.name,
                                                                                         self.record_sort))
                    else:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            self.group_by_measure_field_id.name], domain=search_domain, limit=self.record_limit)
                    for model_data_id in model_data_ids:
                        treemap_dict = {}
                        pie_dict = {}
                        if self.calculation_type == 'sum':
                            measure_data_list.append(model_data_id.get(self.measure_model_field_ids[0].name))
                            treemap_dict.update({'value': model_data_id.get(self.measure_model_field_ids[0].name)})
                            pie_dict.update({'value': model_data_id.get(self.measure_model_field_ids[0].name)})
                        else:
                            measure_data_list.append(
                                model_data_id.get("{}_count".format(self.group_by_measure_field_id[0].name)))
                            treemap_dict.update(
                                {'value': model_data_id.get(
                                    "{}_count".format(self.group_by_measure_field_id[0].name))})
                            pie_dict.update(
                                {'value': model_data_id.get("{}_count".format(self.group_by_measure_field_id[0].name))})
                        max_data.append(max(measure_data_list))
                        label = model_data_id.get(self.group_by_measure_field_id.name)
                        model_label_list.append(model_data_id.get(self.group_by_measure_field_id.name))
                        treemap_dict.update({'name': model_data_id.get(self.group_by_measure_field_id.name)})
                        pie_dict.update({'name': model_data_id.get(self.group_by_measure_field_id.name)})
                        treemap_data_list.append(treemap_dict)
                        measure_and_label_list.append(pie_dict)
            else:
                if self.group_by_filter:
                    if self.record_sort_field and self.record_sort:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter)],
                                                                                     domain=search_domain,
                                                                                     limit=self.record_limit,
                                                                                     orderby='{} {}'.format(
                                                                                         self.record_sort_field.name,
                                                                                         self.record_sort))
                    else:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter)],
                                                                                     domain=search_domain,
                                                                                     limit=self.record_limit)
                    for model_data_id in model_data_ids:
                        treemap_dict = {}
                        pie_dict = {}
                        if self.calculation_type == 'sum':
                            measure_data_list.append(model_data_id.get(self.measure_model_field_ids[0].name))
                            treemap_dict.update({'value': model_data_id.get(self.measure_model_field_ids[0].name)})
                            pie_dict.update({'value': model_data_id.get(self.measure_model_field_ids[0].name)})
                        else:
                            measure_data_list.append(
                                model_data_id.get("{}_count".format(self.group_by_measure_field_id[0].name)))
                            treemap_dict.update(
                                {'value': model_data_id.get(
                                    "{}_count".format(self.group_by_measure_field_id[0].name))})
                            pie_dict.update(
                                {'value': model_data_id.get("{}_count".format(self.group_by_measure_field_id[0].name))})
                        max_data.append(max(measure_data_list))
                        label = model_data_id.get(
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter))

                        model_label_list.append(model_data_id.get(
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter)))
                        treemap_dict.update({'name': model_data_id.get(
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter))})
                        pie_dict.update({'name': model_data_id.get(
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter))})

                        treemap_data_list.append(treemap_dict)
                        measure_and_label_list.append(pie_dict)

        if self.chart_type == 'column':
            if not stack_value:
                stack_value = self.group_by_measure_field_id.field_description,
            data_dict = {
                'type': 'bar',
                'label': {'show': True if self.is_show_datalabels else False},
                'stack': stack_value if self.is_stack_chart else False,
                'emphasis': {
                    'focus': 'series'
                },
                'name': self.group_by_measure_field_id.field_description,
                'data': measure_data_list
            }
            new_measure_data_list.append(data_dict)

        elif self.chart_type == 'bar':
            if not stack_value:
                stack_value = self.group_by_measure_field_id.field_description,
            data_dict = {
                'type': self.chart_type,
                'label': {'show': True if self.is_show_datalabels else False},
                'stack': stack_value if self.is_stack_chart else False,
                'emphasis': {
                    'focus': 'series'
                },
                'name': self.group_by_measure_field_id.field_description,
                'data': measure_data_list
            }
            new_measure_data_list.append(data_dict)
        else:
            data_dict = {
                'type': self.chart_type,
                'name': self.group_by_measure_field_id.field_description,
                'data': measure_data_list
            }
            new_measure_data_list.append(data_dict)
        if self.chart_type in ['bar', 'line', 'column']:
            return_dict = {
                'data_list': new_measure_data_list,
                'model_label_list': model_label_list,
                'max': max(max_data if max_data else [0])
            }
            return json.dumps(return_dict)

    def _group_by_data_list_view(self, search_domain):
        header_list = []
        data_list = []
        if self.group_by_measure_field_id:
            header_list.append(self.group_by_measure_field_id.field_description)
            for list_view_field_id in self.measure_model_field_ids:
                header_list.append(list_view_field_id.field_description)
            if self.group_by_measure_field_id.ttype not in ['datetime', 'date']:
                if self.record_sort_field and self.record_sort:
                    model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                        self.group_by_measure_field_id.name], domain=search_domain, limit=self.record_limit,
                                                                                 orderby='{} {}'.format(
                                                                                     self.record_sort_field.name,
                                                                                     self.record_sort))
                else:
                    model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                        self.group_by_measure_field_id.name], domain=search_domain, limit=self.record_limit)
                if self.group_by_measure_field_id.ttype in ['many2one']:
                    for model_data_id in model_data_ids:
                        # TODO data value find in next execution
                        data = model_data_id.get(self.group_by_measure_field_id.name) if not model_data_id.get(
                            self.group_by_measure_field_id.name) else \
                            model_data_id.get(self.group_by_measure_field_id.name)[1]
                        model_data_list = [str(data)]
                        for measure_model_field_id in self.measure_model_field_ids:
                            model_data_list.append(model_data_id.get(measure_model_field_id.name))
                        data_list.append(model_data_list)
                else:
                    for model_data_id in model_data_ids:
                        data = model_data_id.get(self.group_by_measure_field_id.name)
                        model_data_list = [data]
                        for measure_model_field_id in self.measure_model_field_ids:
                            model_data_list.append(model_data_id.get(measure_model_field_id.name))
                        data_list.append(model_data_list)
            else:
                if self.group_by_filter:
                    if self.record_sort_field and self.record_sort:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter)],
                                                                                     domain=search_domain,
                                                                                     limit=self.record_limit,
                                                                                     orderby='{} {}'.format(
                                                                                         self.record_sort_field.name,
                                                                                         self.record_sort))
                    else:
                        model_data_ids = self.env[self.ir_model_id.model].read_group(fields=[], groupby=[
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter)],
                                                                                     domain=search_domain,
                                                                                     limit=self.record_limit)
                    for model_data_id in model_data_ids:
                        model_data_list = []
                        model_data_list.append(model_data_id.get(
                            '{}:{}'.format(self.group_by_measure_field_id.name, self.group_by_filter)))
                        for measure_model_field_id in self.measure_model_field_ids:
                            model_data_list.append(model_data_id.get(measure_model_field_id.name))
                        data_list.append(model_data_list)
        return_dict = {
            'header_field_list': header_list,
            'measure_data_list': data_list
        }

        return json.dumps(return_dict)

    @api.onchange('is_group_by_data')
    def _onchange_is_group_by_data(self):
        self.calculation_type = False
        if not self.is_group_by_data:
            self.group_by_measure_field_id = False
            self.group_by_filter = False
        else:
            self.label_model_field_id = False
