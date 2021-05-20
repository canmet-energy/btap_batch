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

        self.par_coord_data = None
        self.table_metrics = None
        self.pc_metrics = []
        self.metrics = [
            {'filter': 'all', 'label': 'Index', 'col_name': 'index'},

            # Code Tier
            {'filter': 'targets', 'label': 'TierLevel', 'col_name': 'baseline_necb_tier'},

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

        # Enter in the full path to your Excel analysis output file.
        OUTPUT_XLSX = r'C:\Users\plopez\test\btap_batch\src\resources\output.xlsx'

        # This loads the information from the BTAPBatch Excel output. It strips the headers col names, rounds the floats, and  encodes
        # string values into numeric to make it easy to graph.
        self.df = pd.read_excel(open(OUTPUT_XLSX, 'rb'),
                                sheet_name='btap_data')
        # Round to 3 decimal places
        self.df = self.df.round(3)
        self.df.reset_index(drop=True, inplace=True)
        # create index for easier lookup.
        self.df['index'] = list(range(len(self.df.index)))

        # This piece of code will create numeric map column for each string column. The new column will have the suffix
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

    def get_pc_metrics(self):
        pc_metrics = []
        for metric in self.metrics:
            if metric['col_name'] in self.df.columns:
                if self.df[metric['col_name']].nunique() > 1:
                    pc_metrics.append(metric)
        return pc_metrics

    def get_table_metrics(self):
        self.table_metrics = copy.deepcopy(self.metrics)
        self.table_metrics.append(
            {'filter': 'output', 'label': 'Link', 'col_name': 'link', 'type': 'text', 'presentation': 'markdown'})
        return self.table_metrics

    def get_table_columns(self):
        columns = []
        # print(self.table_metrics)
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
                    if self.df[item['col_name']].dtypes == object:
                        metric = dict(label=item['label'],
                                      tickvals=self.df[item["col_name"] + '_code'].unique(),
                                      ticktext=self.df[item['col_name']].unique(),
                                      values=self.df[item["col_name"] + '_code'],
                                      visible=visible)
                    else:
                        metric = dict(label=item['label'],
                                      values=self.df[item['col_name']],
                                      visible=visible
                                      )
                    pc_list.append(metric)
            dimensions = list(pc_list)
        else:
            # Get labels that should be visible.

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

    def get_pc_filtered_data(self):
        self.df_filt = self.df.copy()
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

#### Parallel Coordinates Methods.
def get_pc_graph_form_group(data):
    list_of_domains = list(set([d['filter'] for d in data.get_pc_metrics()]))
    options = [{'label': item, 'value': item} for item in list_of_domains]

    children = [
        dbc.FormGroup(
            [
                dbc.Label("Filter"),
                dcc.Dropdown(
                    id='pc_graph_form_domain',
                    options=options,
                    value="all"
                )
            ]
        )
    ]
    return children

def get_pc_chart(data):
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
                color=data.df['energy_eui_total_gj_per_m_sq'],
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
def get_scatter_graph(data=None):
    pc_filtered_data = data.get_pc_filtered_data()
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
            hover_data=['index', 'baseline_necb_tier', 'cost_equipment_total_cost_per_m_sq',
                        'cost_utility_neb_total_cost_per_m_sq', 'baseline_savings_energy_cost_per_m_sq',
                        'energy_eui_total_gj_per_m_sq', 'baseline_energy_percent_better',
                        'cost_utility_ghg_total_kg_per_m_sq',
                        'baseline_ghg_percent_better', 'energy_peak_electric_w_per_m_sq',
                        'baseline_peak_electric_percent_better',
                        ':building_type', ':template', ':primary_heating_fuel', ':rotation_degrees', ':scale_x',
                        ':scale_y',
                        ]

            # hover_data=[d['col_name'] for d in metrics if 'col_name' in d]
            # marginal_y="histogram",
            # marginal_x="histogram"
        )
        scatter_graph.update_traces(marker=dict(size=12,
                                                line=dict(width=2,
                                                          color='DarkSlateGrey')),
                                    selector=dict(mode='markers'))
    return scatter_graph

def get_scatter_graph_form_group(data=None):
    options = [
        {'label': d['label'], 'value': d['col_name']} for d in data.metrics
        if 'col_name' in d
    ]
    children = [
        dbc.FormGroup(
            [
                dbc.Label("Color variable"),
                dcc.Dropdown(
                    id='xy_scatter_color_dropdown',
                    options=options,
                    value=":dcv_type"
                )
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("X-Axis"),
                dcc.Dropdown(
                    id='xy_scatter_x_axis_dropdown',
                    options=options,
                    value="energy_eui_total_gj_per_m_sq"
                )
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Y-Axis"),
                dcc.Dropdown(
                    id='xy_scatter_y_axis_dropdown',
                    options=options,
                    value="cost_equipment_total_cost_per_m_sq"
                )
            ]
        )
    ]
    return children

#### DataTable
def init_data_table(id='data-table',data=None):
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


#### Main

# Load Sample data used by dash library.
data = Data()

# Set up app and use standard BOOTSTRAP theme.
app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# Basic HTMl Bootstrap / Layout
app.layout = html.Div([
    dcc.Tabs(
        [
            dcc.Tab(
                label='Design Contraints',
                children=[
                    dbc.Row(
                        dbc.Col(
                            children=[
                                dbc.Card(
                                    id='pc-graph-form',
                                    children=get_pc_graph_form_group(data),
                                    body=True,
                                )
                            ],
                            md=2
                        )
                    ),

                    # PC Chart layout
                    dbc.Row(
                        dbc.Col(
                            [

                                html.Div(id='scenario_count'),
                                dcc.Graph(
                                    id='pc-graph'
                                )
                            ],
                            align="center",
                        )
                    )
                ]
            ),
            # Scatter Graph Layout
            dcc.Tab(label='Performance Analysis', children=[
                dbc.Row(
                    [
                        dbc.Col(
                            children=[
                                html.H3(
                                    children='X-Y Scatter Viewer'
                                )
                            ],
                            md=10
                        )
                    ],
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            children=[
                                dbc.Card(
                                    id='scatter-graph-form',
                                    children=get_scatter_graph_form_group(data),
                                    body=True,
                                )
                            ],
                            md=2
                        ),
                        dbc.Col(
                            children=[
                                dcc.Graph(id='scatter-graph')
                            ],
                            md=10)
                    ],
                    align="center",
                )]),
            dcc.Tab(label='Solution Sets', children=[
                # Datatable Layout
                dbc.Row(
                    [
                        dbc.Col(
                            children=[
                                init_data_table(id='data-table',data=data)
                            ],
                            md=12
                        )
                    ],
                    align="center",
                )])])
],
    style={'padding': '20px 20px 20px 20px'}  # Added in style padding to ignore the cutoffs
)


## Callback / Updates
@app.callback(
    # Update XY Scatter Graph.
    Output(component_id='scatter-graph', component_property='figure'),
    # Update columns, data and style in datatable.
    Output(component_id='data-table', component_property='data'),
    # Update PC figure.
    Output(component_id='pc-graph', component_property='figure'),
    # Update Scenario Count.
    Output(component_id='scenario_count', component_property='children'),

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
        get_scatter_graph(data),  # Scatter figure
        data.get_pc_filtered_data().to_dict('records'),  # Update Datatable with records that may be filtered.
        get_pc_chart(data=data),  # Parallel Coords Figure
        'Scenarios: {}'.format(len(data.get_pc_filtered_data().to_dict('records')))
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
