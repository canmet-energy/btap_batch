import pandas as pd
import numpy as np
import dash
import plotly.express as px
import plotly.graph_objects as go
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from sklearn.preprocessing import LabelEncoder
import copy


class Data:
    def __init__(self):
        # Enter in the full path to your Excel analysis output file.
        OUTPUT_XLSX = r'C:\Users\plopez\test\btap_batch\src\test\test_output\local_elimination\elimination_example\ee4079cc-2961-4fc4-9a4d-7b6454b8cf31\output\output.xlsx'
        # Variable to store the para cords state.
        self.par_coord_data = None
        # Variable to store scatter graph inputs.
        self.xy_scatter_x_axis_dropdown = None
        self.xy_scatter_y_axis_dropdown = None
        self.xy_scatter_color_dropdown = None
        # Variable to store pc graph filter domain input
        self.pc_graph_form_domain = None
        # Optimized filtered dataframe
        self.opt_df = None
        # Metrics to be used by dashboard. Columns should match excel/btap_data.json column names
        self.metrics = [
            {'filter': 'all', 'label': 'Index', 'col_name': 'index'},

            # Code Tier
            {'filter': 'targets', 'label': 'NECB\'17 Tier', 'col_name': 'baseline_necb_tier'},

            # Economics
            {'filter': 'targets', 'label': 'MaterialCost($/m2)', 'col_name': 'cost_equipment_total_cost_per_m_sq'},
            {'filter': 'targets', 'label': 'UtilCost($/m2)', 'col_name': 'cost_utility_neb_total_cost_per_m_sq'},
            {'filter': 'targets', 'label': 'UtilCostSavings($/m2)',
             'col_name': 'baseline_savings_energy_cost_per_m_sq'},
            # Energy
            {'filter': 'targets', 'label': 'EUI(GJ/m2)', 'col_name': 'energy_eui_total_gj_per_m_sq'},
            {'filter': 'targets', 'label': 'EUI%Better', 'col_name': 'baseline_energy_percent_better'},
            # GHGs
            {'filter': 'targets', 'label': 'UtilGHG(kg/m2)', 'col_name': 'cost_utility_ghg_total_kg_per_m_sq'},
            {'filter': 'targets', 'label': 'UtilGHG%Better', 'col_name': 'baseline_ghg_percent_better'},
            # Peak
            {'filter': 'targets', 'label': 'ElecPeak(W/m2)', 'col_name': 'energy_peak_electric_w_per_m_sq'},
            {'filter': 'targets', 'label': 'ElecPeak%Better', 'col_name': 'baseline_peak_electric_percent_better'},

            # Building Selection
            {'filter': 'input', 'label': 'BuildingType', 'col_name': ':building_type'},
            {'filter': 'input', 'label': 'Template', 'col_name': ':template'},
            {'filter': 'input', 'label': 'BaselineHeatingFuel', 'col_name': ':primary_heating_fuel'},

            # Geometry
            {'filter': 'geometry', 'label': 'Rotation', 'col_name': ':rotation_degrees'},
            {'filter': 'geometry', 'label': 'ScaleX', 'col_name': ':scale_x'},
            {'filter': 'geometry', 'label': 'ScaleY', 'col_name': ':scale_y'},
            {'filter': 'geometry', 'label': 'ScaleZ', 'col_name': ':scale_z'},

            # Envelope metrics
            {'filter': 'envelope', 'label': 'RoofConductance',
             'col_name': 'env_outdoor_roofs_average_conductance-w_per_m_sq_k'},
            {'filter': 'envelope', 'label': 'WallConductance.',
             'col_name': 'env_outdoor_walls_average_conductance-w_per_m_sq_k'},
            {'filter': 'envelope', 'label': 'WindowConductance.',
             'col_name': 'env_outdoor_windows_average_conductance-w_per_m_sq_k'},
            {'filter': 'envelope', 'label': 'GroundWall', 'col_name': ':ground_wall_cond'},
            {'filter': 'envelope', 'label': 'GroundFloor', 'col_name': ':ground_floor_cond'},
            {'filter': 'envelope', 'label': 'GroundRoof', 'col_name': ':ground_roof_cond'},
            {'filter': 'envelope', 'label': 'SkylightConductance', 'col_name': ':skylight_cond'},
            {'filter': 'envelope', 'label': 'Skylight SHGC', 'col_name': ':fixed_wind_solar_trans'},
            {'filter': 'envelope', 'label': 'Window SHGC', 'col_name': ':skylight_solar_trans'},
            {'filter': 'envelope', 'label': 'Skylight-Roof Ratio', 'col_name': ':srr_set'},
            {'filter': 'envelope', 'label': 'Window-Wall Ratio', 'col_name': ':fdwr_set'},
            # Load Metrics
            {'filter': 'loads', 'label': 'DaylightControl', 'col_name': ':daylighting_type'},
            {'filter': 'loads', 'label': 'LightingType', 'col_name': ':lights_type'},
            {'filter': 'loads', 'label': 'Light Scaling', 'col_name': ':lights_scale'},
            {'filter': 'loads', 'label': 'Occupancy Scale', 'col_name': ':occupancy_loads_scale'},
            {'filter': 'loads', 'label': 'Occupancy Scale', 'col_name': ':electrical_loads_scale'},
            {'filter': 'loads', 'label': 'OutdoorAir Scale', 'col_name': ':oa_scale'},
            {'filter': 'loads', 'label': 'Infiltration Scale', 'col_name': ':infiltration_scale'},

            # HVAC Metrics
            {'filter': 'hvac', 'label': 'HVAC System', 'col_name': ':ecm_system_name'},
            {'filter': 'hvac', 'label': 'Demand Control Ventilation', 'col_name': ':dcv_type'},
            {'filter': 'hvac', 'label': 'ERV', 'col_name': ':erv_package'},
            {'filter': 'hvac', 'label': 'Boiler Package', 'col_name': ':boiler_eff'},
            {'filter': 'hvac', 'label': 'Furnace Package', 'col_name': ':furnace_eff'},
            {'filter': 'hvac', 'label': 'SHW Package', 'col_name': ':shw_eff'},
            {'filter': 'hvac', 'label': 'Advanced DX', 'col_name': ':adv_dx_units'},
            {'filter': 'hvac', 'label': 'Chiller Type', 'col_name': ':chiller_type'},
            {'filter': 'hvac', 'label': 'Natural Ventilation', 'col_name': ':nv_type'},

            # Renewables
            {'filter': 'renewables', 'label': 'GroundPV', 'col_name': ':pv_ground_type'},

            # Code Tiers
            # {'filter': 'output', 'label': 'URL', 'col_name': 'datapoint_output_url'},
        ]

        # This loads the information from the BTAPBatch Excel output. It strips the headers col names, rounds the floats, and  encodes
        # string values into numeric to make it easy to graph.
        self.df = pd.read_excel(open(OUTPUT_XLSX, 'rb'),
                                sheet_name='btap_data')
        # Round to 3 decimal places
        self.df = self.df.round(3)
        # Reset index
        self.df.reset_index(drop=True, inplace=True)
        # create index for easier lookup.
        self.df['index'] = list(range(len(self.df.index)))

        # This piece of code will create numeric map column for each string
        # column. The new column will have the suffix
        # '_code' as the name
        for col_name in [col for col, dt in self.df.dtypes.items() if dt == object]:
            if not col_name in ['run_options']:
                self.df[f'{col_name}_code'] = LabelEncoder().fit_transform(self.df[col_name])

        # Create markdown hyperlink column from url.
        # format dataframe column of urls so that it displays as hyperlink
        def display_links(df):
            links = df['datapoint_output_url'].to_list()
            rows = []
            for x in links:
                link = '[Link](' + str(x) + ')'
                rows.append(link)
            return rows

        self.df['link'] = display_links(self.df)

        # Create a hash from the metrics data so it can be easily used.
        self.labels = {d['col_name']: d['label'] for d in self.metrics}

    def get_opt_df(self):
        if not isinstance(self.opt_df, pd.DataFrame):
            self.opt_df = self.df.copy()
            # filter by optimized or parametric runs.
            self.opt_df = self.opt_df.loc[self.opt_df[':algorithm_type'] == 'nsga2']
        return self.opt_df

    def get_pc_metrics(self):
        pc_metrics = []
        for metric in self.metrics:
            if metric['col_name'] in self.get_opt_df().columns:
                if self.get_opt_df()[metric['col_name']].nunique() > 1:
                    pc_metrics.append(metric)
        return pc_metrics

    def get_table_metrics(self):
        table_metrics = copy.deepcopy(self.metrics)
        table_metrics.append(
            {'filter': 'output', 'label': 'Link', 'col_name': 'link', 'type': 'text', 'presentation': 'markdown'})
        return table_metrics

    def get_table_columns(self):
        columns = []
        for i in self.get_table_metrics():
            columns.append(
                {"name": i['label'], "id": i['col_name'], "deletable": True, "selectable": True, 'type': 'text',
                 'presentation': 'markdown'})
        return columns

    def get_pc_dimensions(self):
        # sets up initial state of figure or passes the existing state to new figure object.
        dimensions = None
        # If there are no selections yet.. Show all scenarios.
        if self.par_coord_data == None:
            pc_list = []
            for item in data.get_pc_metrics():
                visible = True
                if item['col_name'] != 'index':
                    if self.get_opt_df()[item['col_name']].dtypes == object:
                        metric = dict(label=item['label'],
                                      tickvals=self.get_opt_df()[item["col_name"] + '_code'].unique(),
                                      ticktext=self.get_opt_df()[item['col_name']].unique(),
                                      values=self.get_opt_df()[item["col_name"] + '_code'],
                                      visible=visible)
                    else:
                        metric = dict(label=item['label'],
                                      values=self.get_opt_df()[item['col_name']],
                                      visible=visible
                                      )
                    pc_list.append(metric)
            dimensions = list(pc_list)
        else:
            # Get labels that should be visible in graph.

            if self.pc_graph_form_domain == 'all':
                labels_on = [d['label'] for d in self.get_pc_metrics()]
            else:
                labels_on = [d['label'] for d in self.get_pc_metrics() if d['filter'] == data.pc_graph_form_domain]

            for item in self.par_coord_data['data'][0]['dimensions']:
                # print(item)
                if item['label'] in labels_on:
                    item['visible'] = True
                else:
                    item['visible'] = False

            dimensions = self.par_coord_data['data'][0]['dimensions']
        return dimensions

    def update_datamodel(self,
                         xy_scatter_x_axis_dropdown=None,
                         xy_scatter_y_axis_dropdown=None,
                         xy_scatter_color_dropdown=None,
                         pc_graph_form_domain=None,
                         par_coord_data=None):
        if xy_scatter_x_axis_dropdown != None: self.xy_scatter_x_axis_dropdown = xy_scatter_x_axis_dropdown
        if xy_scatter_y_axis_dropdown != None: self.xy_scatter_y_axis_dropdown = xy_scatter_y_axis_dropdown
        if xy_scatter_color_dropdown != None: self.xy_scatter_color_dropdown = xy_scatter_color_dropdown
        if pc_graph_form_domain != None: self.pc_graph_form_domain = pc_graph_form_domain
        if par_coord_data != None: self.par_coord_data = par_coord_data

    def get_spreadsheet_data(self):
        self.df_filt = self.get_opt_df().copy()
        # Skip if state does not exist. This will happen on initialization of graph.
        if self.par_coord_data != None and 'data' in self.par_coord_data:
            # Create Filter data based on PC dimension contraints.
            # Iterate through all dimensions in pc chart.
            for d in self.par_coord_data['data'][0]['dimensions']:
                # Determine if there are constraints on dimension.
                if 'constraintrange' in d:
                    # Create mask dataframe for item that are selected.
                    crs = np.array(d['constraintrange'])
                    if crs.ndim == 1:
                        crs = [crs]
                    masks = []
                    for cr in crs:
                        key = {v: k for k, v in self.labels.items()}[d['label']]
                        # If a string coverted column, use the *_code version.
                        if self.df_filt[key].dtypes == object:
                            key = key + '_code'
                        masks.append(self.df_filt[key].between(*cr))
                    # Apply mask to our cloned dataframe.
                    self.df_filt = self.df_filt[np.logical_or.reduce(masks)]
        return self.df_filt

    def xy_scatter_options(self):
        return [{'label': d['label'], 'value': d['col_name']} for d in self.metrics if 'col_name' in d]

    def pc_filter_options(self):
        return [{'label': item, 'value': item} for item in list(set([d['filter'] for d in data.get_pc_metrics()]))]

    def get_building_types(self):
        return [{'label': d, 'value': d} for d in self.df[':building_type'].unique().tolist()]

    def get_epw_locations(self):
        return [{'label': d, 'value': d} for d in self.df[':epw_file'].unique().tolist()]

    def get_epw_locations(self):
        return [{'label': d, 'value': d} for d in self.df[':epw_file'].unique().tolist()]

    def get_primary_heating_fuels(self):
        return [{'label': d, 'value': d} for d in self.df[':primary_heating_fuel'].unique().tolist()]


class Figures:

    #### Parallel Coordinates Methods.

    def get_pc_chart(self, data=None):
        # If no data show nothing.
        if data.df.index.empty:
            # If empty, let user know and create blank figure.
            scatter_graph = px.scatter()
            scatter_graph.layout.annotations = [dict(text='empty dataframe', showarrow=False)]
            return scatter_graph

        # Creates new figure.
        fig = go.Figure(
            layout=go.Layout(
                title=go.layout.Title(text="Scenario Pathways", font=dict(size=25, color='white')),
                height=600,  # px
            ),
            data=go.Parcoords(
                # Color lines based on eui.
                line=dict(
                    color=data.get_opt_df()['energy_eui_total_gj_per_m_sq'],
                    colorscale=[
                        [0, 'green'],
                        [0.5, 'yellow'],
                        [1.0, 'red']
                    ]
                ),
                dimensions=data.get_pc_dimensions(),
            ),
        )
        fig.update_traces(labelangle=20, selector=dict(type='parcoords'))
        # fig.update_traces(labelfont_size=10, selector=dict(type='parcoords'))
        # fig.update_traces(rangefont_size=5, selector=dict(type='parcoords'))
        # fig.update_traces(tickfont_size=5, selector=dict(type='parcoords'))
        # fig.update_traces(tickfont_color='white', selector=dict(type='parcoords'))
        # fig.update_traces(line_colorbar_tickfont_size=100, selector=dict(type='parcoords'))
        # fig.update_traces(labelside='bottom', selector=dict(type='parcoords'))
        # fig.update_traces(line_colorbar_ticklabelposition='outside', selector=dict(type='parcoords'))
        # fig.update_traces(line_colorbar_tickformatstops=list(...), selector=dict(type='parcoords'))
        return fig

    #### Scatter Plot Methods
    def get_scatter_graph(self, data=None):
        pc_filtered_data = data.get_spreadsheet_data()
        xy_scatter_color_dropdown = data.xy_scatter_color_dropdown
        xy_scatter_x_axis_dropdown = data.xy_scatter_x_axis_dropdown
        xy_scatter_y_axis_dropdown = data.xy_scatter_y_axis_dropdown

        scatter_graph = None
        # Create/Update standard scatter graph with filtered data.
        if pc_filtered_data.index.empty:
            # If empty, let user know and create blank figure.
            scatter_graph = px.scatter()
            scatter_graph.layout.annotations = [dict(text='filtering results in empty dataframe', showarrow=False)]
        else:
            scatter_graph = px.scatter(
                data_frame=pc_filtered_data,
                x=xy_scatter_x_axis_dropdown,
                y=xy_scatter_y_axis_dropdown,
                color=xy_scatter_color_dropdown,
                # hover_data=[d['col_name'] for d in data.metrics if 'col_name' in d],
                hover_data=[pc_filtered_data['index']],
                marginal_y="histogram",
                marginal_x="histogram"
            )
            scatter_graph.update_traces(marker=dict(size=12,
                                                    line=dict(width=2,
                                                              color='DarkSlateGrey')),
                                        selector=dict(mode='markers'))
        return scatter_graph

    #### DataTable
    def init_data_table(self, id='data-table', data=None):
        start_table_df = pd.DataFrame(columns=['Start Column'])

        style_cell_conditional = []
        for col in data.df.columns:
            name_length = len(col)
            pixel = 50 + round(name_length * 8)
            pixel = str(pixel) + "px"
            style_cell_conditional.append({'if': {'column_id': col}, 'minWidth': pixel})

        data_table = dash_table.DataTable(data=start_table_df.to_dict('records'),
                                          columns=data.get_table_columns(),
                                          id=id,
                                          style_table={
                                              'overflowY': 'scroll',
                                              'overflowX': 'scroll',
                                              'height': 600,
                                          },
                                          fixed_rows={'headers': True},
                                          editable=True,
                                          filter_action="native",
                                          sort_action="native",
                                          sort_mode="multi",
                                          column_selectable="single",
                                          row_selectable="multi",
                                          row_deletable=True,
                                          selected_columns=[],
                                          selected_rows=[],
                                          page_action="native",
                                          export_format="csv",
                                          style_cell_conditional=style_cell_conditional
                                          )

        return data_table

    def get_elimination_figure(self, id='elimination_stacked_bar', data=None):
        elim_df = copy.deepcopy(data.df)
        # Filter by :analysis_name = elimination
        # :scenario
        elim_df = elim_df.loc[elim_df[':algorithm_type'] == 'elimination']
        if elim_df.empty:
            fig = px.bar()
            fig.layout.annotations = [dict(text='Elimination data not available.', showarrow=False)]
            return fig

        fig = px.bar(elim_df,
                     x=":scenario",
                     y=['energy_eui_additional_fuel_gj_per_m_sq',
                        'energy_eui_cooling_gj_per_m_sq',
                        'energy_eui_district_cooling_gj_per_m_sq',
                        'energy_eui_district_heating_gj_per_m_sq',
                        'energy_eui_fans_gj_per_m_sq',
                        'energy_eui_heat recovery_gj_per_m_sq',
                        'energy_eui_heating_gj_per_m_sq',
                        'energy_eui_interior equipment_gj_per_m_sq',
                        'energy_eui_interior lighting_gj_per_m_sq',
                        'energy_eui_pumps_gj_per_m_sq',
                        'energy_eui_water systems_gj_per_m_sq'],
                     title="Elimination Analysis"
                     )
        fig.update_layout(xaxis={'categoryorder': 'total descending'})
        return fig

    def get_sensitivity_figure(self, id='sensitivity_xy_scatter', data=None):
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        elim_df = copy.deepcopy(data.df)
        # Filter by sensitivity
        elim_df = elim_df.loc[elim_df[':algorithm_type'] == 'sensitivity']
        # If there is no sensitivity analysis.
        if elim_df.empty:
            fig = px.bar()
            fig.layout.annotations = [dict(text='Sensitivity data not available.', showarrow=False)]
            return fig
        ecm_list = elim_df[':scenario'].unique().tolist()
        children = []

        for ecm in ecm_list:
            # Filter by ecm
            ecm_df = elim_df.loc[elim_df[':scenario'] == ecm]

            fig = px.scatter(ecm_df,
                             y='cost_equipment_total_cost_per_m_sq',
                             x="baseline_energy_percent_better",
                             color=ecm,
                             title=ecm
                             )
            # Update size of point/markers.
            fig.update_traces(marker={'size': 15})
            children.append(dcc.Graph(id=ecm, figure=fig))

        return children


#### Main

# Load Sample data used by dash library.
data = Data()
figures = Figures()
# Set up app and use standard BOOTSTRAP theme.
app = dash.Dash("Example",
                external_stylesheets=[dbc.themes.SIMPLEX]
                )

# User Inputs.

# Building and Location Selection

input_building_type = dbc.FormGroup([dbc.Label("Building Type"),
                                     dcc.Dropdown(id='building_type', options=data.get_building_types(),
                                                  value=data.get_building_types()[0]['value'])])
input_weather = dbc.FormGroup([dbc.Label("Weather"),
                               dcc.Dropdown(id='weather', options=data.get_epw_locations(),
                                            value=data.get_epw_locations()[0]['value'])])

input_primary_heating_fuels = dbc.FormGroup([dbc.Label("Baseline Heating Fuel"),
                                             dcc.Dropdown(id='primary_heating_fuel',
                                                          options=data.get_primary_heating_fuels(),
                                                          value=data.get_primary_heating_fuels()[0]['value'])])

# XY Scatter.
input_scatter_y_axis = dbc.FormGroup([dbc.Label("Y-Axis"),
                                      dcc.Dropdown(id='xy_scatter_y_axis_dropdown', options=data.xy_scatter_options(),
                                                   value="cost_equipment_total_cost_per_m_sq")])
input_scatter_x_axis = dbc.FormGroup([dbc.Label("X-Axis"),
                                      dcc.Dropdown(id='xy_scatter_x_axis_dropdown', options=data.xy_scatter_options(),
                                                   value="energy_eui_total_gj_per_m_sq")])
input_scatter_color_dropdown = dbc.FormGroup([dbc.Label("Color"), dcc.Dropdown(id='xy_scatter_color_dropdown',
                                                                               options=data.xy_scatter_options(),
                                                                               value=":dcv_type")])
# PC Inputs
input_pc_filter = dbc.FormGroup(
    [dbc.Label("Filter"), dcc.Dropdown(id='pc_graph_form_domain', options=data.pc_filter_options(), value="all")])

# scenario_counter = dbc.Card( dbc.CardBody([html.H2(id='number_of_scenarios'),]))
scenario_counter = dbc.Button([dbc.Badge("0", color="light", id='number_of_scenarios')], color="primary", )

# Basic HTMl Bootstrap / Layout
app.layout = dbc.Container(fluid=True, children=[
    html.Div([
        dbc.Tabs(
            [
                dbc.Tab(label='Building Baseline Selection',
                        children=[input_building_type, input_weather, input_primary_heating_fuels]),
                dbc.Tab(label='Elimination Analysis', children=[dcc.Graph(id='elimination_stacked_bar')]),
                dbc.Tab(id='sensitivity_analysis_tab',
                        label='Sensitivity Analysis',
                        children=[]),
                dbc.Tab(label='Design Constraints', children=[dbc.Row(
                    [dbc.Col(md=6, children=[input_pc_filter]),
                     dbc.Col(md=6, children=[scenario_counter])]), dcc.Graph(id='pc-graph')]),
                dbc.Tab(label='Data Analysis', children=[dbc.Row(
                    [dbc.Col(md=3, children=[input_scatter_x_axis, input_scatter_y_axis, input_scatter_color_dropdown]),
                     dbc.Col(md=9, children=[dcc.Graph(id='scatter-graph')])])]),
                dbc.Tab(label='Solution Sets', children=[figures.init_data_table(data=data)])
            ]
        )
    ])
])


## Callback / Interactive Updates
@app.callback(
    # Update XY Scatter Graph.
    Output(component_id='scatter-graph', component_property='figure'),
    # Update columns, data and style in datatable.
    Output(component_id='data-table', component_property='data'),
    # Update PC figure.
    Output(component_id='pc-graph', component_property='figure'),
    # Update Scenario Count.
    Output(component_id='number_of_scenarios', component_property='children'),
    # Update Elimination Figure
    Output(component_id='elimination_stacked_bar', component_property='figure'),
    # Update Sensitivity Figure
    Output(component_id='sensitivity_analysis_tab', component_property='children'),

    # Inputs
    Input(component_id='pc-graph', component_property='restyleData'),  # Needed for event call.
    Input(component_id='xy_scatter_x_axis_dropdown', component_property='value'),
    Input(component_id='xy_scatter_y_axis_dropdown', component_property='value'),
    Input(component_id='xy_scatter_color_dropdown', component_property='value'),
    Input(component_id='pc_graph_form_domain', component_property='value'),
    State('pc-graph', 'figure'),
)
def update_graphs(restyledata,
                  xy_scatter_x_axis_dropdown,
                  xy_scatter_y_axis_dropdown,
                  xy_scatter_color_dropdown,
                  pc_graph_form_domain,
                  par_coord_data
                  ):
    # Update the datamodel.
    data.update_datamodel(xy_scatter_x_axis_dropdown=xy_scatter_x_axis_dropdown,
                          xy_scatter_y_axis_dropdown=xy_scatter_y_axis_dropdown,
                          xy_scatter_color_dropdown=xy_scatter_color_dropdown,
                          pc_graph_form_domain=pc_graph_form_domain,
                          par_coord_data=par_coord_data)

    return [
        figures.get_scatter_graph(data=data),  # Scatter figure
        data.get_spreadsheet_data().to_dict('records'),  # Update Datatable with records that may be filtered.
        figures.get_pc_chart(data=data),  # Parallel Coords Figure
        ['Selected Scenarios: {}'.format(len(data.get_spreadsheet_data().to_dict('records')))],
        figures.get_elimination_figure(data=data),
        figures.get_sensitivity_figure(data=data)
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
