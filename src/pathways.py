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

#Enter in the full path to your Excel analysis output file.
OUTPUT_XLSX = r'C:\Users\plopez\test\btap_batch\src\resources\output.xlsx'

# List of metrics add/ change based on btap_data.json file top level fields. Comment out / add items as you see fit for your
# analysis.
metrics = [
    {'domain': 'output', 'label': 'Index', 'col_name': 'index'},

    # Code Tier
    {'domain': 'targets', 'label': 'Tier Level', 'col_name': 'baseline_necb_tier'},

    # Economics
    {'domain': 'targets', 'label': 'Material Cost ($/m2)', 'col_name': 'cost_equipment_total_cost_per_m_sq'},
    {'domain': 'targets', 'label': 'Util Cost ($/m2)', 'col_name': 'cost_utility_neb_total_cost_per_m_sq'},
    {'domain': 'targets', 'label': 'Util Cost Savings ($/m2)', 'col_name': 'baseline_savings_energy_cost_per_m_sq'},
    # Energy
    {'domain': 'targets', 'label': 'EUI GJ/m2', 'col_name': 'energy_eui_total_gj_per_m_sq'},
    {'domain': 'targets', 'label': 'EUI% Better', 'col_name': 'baseline_energy_percent_better'},
    # GHGs
    {'domain': 'targets', 'label': 'GHG kg/m2', 'col_name': 'cost_utility_ghg_total_kg_per_m_sq'},
    {'domain': 'targets', 'label': 'GHG% Better', 'col_name': 'baseline_ghg_percent_better'},
    # Peak
    {'domain': 'targets', 'label': 'ElecPeak W/m2', 'col_name': 'energy_peak_electric_w_per_m_sq'},
    {'domain': 'targets', 'label': 'ElecPeak % Better', 'col_name': 'baseline_peak_electric_percent_better'},

    # Building Selection
    {'domain': 'input', 'label': 'Building Type', 'col_name': ':building_type'},
    {'domain': 'input', 'label': 'Template', 'col_name': ':template'},
    {'domain': 'input', 'label': 'Baseline Heating Fuel', 'col_name': ':primary_heating_fuel'},

    #Geometry
    {'domain': 'geometry', 'label': 'Rotation', 'col_name': ':rotation_degrees'},
    {'domain': 'geometry', 'label': 'ScaleX', 'col_name': ':scale_x'},
    {'domain': 'geometry', 'label': 'ScaleY', 'col_name': ':scale_y'},
    {'domain': 'geometry', 'label': 'ScaleZ', 'col_name': ':scale_z'},

    # Envelope metrics
    {'domain': 'envelope', 'label': 'RoofConductance', 'col_name': 'env_outdoor_roofs_average_conductance-w_per_m_sq_k'},
    {'domain': 'envelope', 'label': 'WallConductance.', 'col_name': 'env_outdoor_walls_average_conductance-w_per_m_sq_k'},
    {'domain': 'envelope', 'label': 'WindowConductance.', 'col_name': 'env_outdoor_windows_average_conductance-w_per_m_sq_k'},
    {'domain': 'envelope', 'label': 'GroundWall', 'col_name': ':ground_wall_cond'},
    {'domain': 'envelope', 'label': 'GroundFloor', 'col_name': ':ground_floor_cond'},
    {'domain': 'envelope', 'label': 'GroundRoof', 'col_name': ':ground_roof_cond'},
    {'domain': 'envelope', 'label': 'SkylightConductance', 'col_name': ':skylight_cond'},
    {'domain': 'envelope', 'label': 'Skylight SHGC', 'col_name': ':fixed_wind_solar_trans'},
    {'domain': 'envelope', 'label': 'Window SHGC', 'col_name': ':skylight_solar_trans'},
    {'domain': 'envelope', 'label': 'Skylight-Roof Ratio', 'col_name': ':srr_set'},
    {'domain': 'envelope', 'label': 'Window-Wall Ratio', 'col_name': ':fdwr_set'},
    # Load Metrics
    {'domain': 'loads', 'label': 'DaylightControl', 'col_name': ':daylighting_type'},
    {'domain': 'loads', 'label': 'LightingType', 'col_name': ':lights_type'},
    {'domain': 'loads', 'label': 'Light Scaling', 'col_name': ':lights_scale'},
    {'domain': 'loads', 'label': 'Occupancy Scale', 'col_name': ':occupancy_loads_scale'},
    {'domain': 'loads', 'label': 'Occupancy Scale', 'col_name': ':electrical_loads_scale'},
    {'domain': 'loads', 'label': 'OutdoorAir Scale', 'col_name': ':oa_scale'},
    {'domain': 'loads', 'label': 'Infiltration Scale', 'col_name': ':infiltration_scale'},

    # HVAC Metrics
    {'domain': 'hvac', 'label': 'HVAC System', 'col_name': ':ecm_system_name'},
    {'domain': 'hvac', 'label': 'Demand Control Ventilation', 'col_name': ':dcv_type'},
    {'domain': 'hvac', 'label': 'ERV', 'col_name': ':erv_package'},
    {'domain': 'hvac', 'label': 'Boiler Package', 'col_name': ':boiler_eff'},
    {'domain': 'hvac', 'label': 'Furnace Package', 'col_name': ':furnace_eff'},
    {'domain': 'hvac', 'label': 'SHW Package', 'col_name': ':shw_eff'},
    {'domain': 'hvac', 'label': 'Advanced DX', 'col_name': ':adv_dx_units'},
    {'domain': 'hvac', 'label': 'Chiller Type', 'col_name': ':chiller_type'},
    {'domain': 'hvac', 'label': 'Natural Ventilation', 'col_name': ':nv_type'},




    #Renewables
    {'domain': 'renewables', 'label': 'GroundPV', 'col_name': ':pv_ground_type'},

    # Code Tiers
    #{'domain': 'output', 'label': 'URL', 'col_name': 'datapoint_output_url'},
]





table_metrics = copy.deepcopy(metrics)
table_metrics.append({'domain': 'output', 'label': 'Link', 'col_name': 'link', 'type':'text','presentation':'markdown'})

# Please do not modify anything below.


# This method tries to guess the width of the columns in the data-table figure.
def create_conditional_style(df):
    style = []
    for col in df.columns:
        name_length = len(col)
        pixel = 50 + round(name_length * 8)
        pixel = str(pixel) + "px"
        style.append({'if': {'column_id': col}, 'minWidth': pixel})
    return style


# This loads the information from the BTAPBatch Excel output. It strips the headers col names, rounds the floats, and  encodes
# string values into numeric to make it easy to graph.
def load_dataframe():
    df = pd.read_excel(open(OUTPUT_XLSX, 'rb'),
                  sheet_name='btap_data')
    # Round to 3 decimal places
    df = df.round(3)
    df.reset_index(drop=True, inplace=True)
    #create index for easier lookup.
    df['index'] = list(range(len(df.index)))


    # This piece of code will create numeric map column for each string column. The new column will have the suffix
    # '_code' as the name
    for col_name in [col for col, dt in df.dtypes.items() if dt == object]:
        if not col_name in ['run_options']:
            df[f'{col_name}_code'] = LabelEncoder().fit_transform(df[col_name])

    # Create markdown hyperlink column from url.
    #format dataframe column of urls so that it displays as hyperlink
    def display_links(df):
        links = df['datapoint_output_url'].to_list()
        rows = []
        for x in links:
            link = '[Link](' +str(x) + ')'
            rows.append(link)
        return rows

    df['link'] = display_links(df)

    # Done configuring dataframe. Return it.
    return df

#### Parallel Coordinates Methods.
# This method creates the parallel co-ordinate chart.
def get_pc_chart(df, color=None, par_coord_data=None):
    pc_metrics = []

    # Eliminate axises with one value.

    for metric in metrics:
        if metric['col_name'] in df.columns:
            if df[metric['col_name']].nunique() > 1:
                pc_metrics.append(metric)


    if df.index.empty:
        # If empty, let user know and create blank figure.
        scatter_graph = px.scatter()
        scatter_graph.layout.annotations = [dict(text='empty dataframe', showarrow=False)]
        return scatter_graph

    line = None
    if color == None:
        line = dict(
            color=df['energy_eui_total_gj_per_m_sq'],
            colorscale=[
                [0, 'green'],
                [0.5, 'yellow'],
                [1.0, 'red']
            ]
        )

    # sets up initial state of figure or passes the existing state to new figure object.
    dimensions = None
    if par_coord_data == None:
        pc_list = []
        for item in pc_metrics:
            if item['col_name'] != 'index':
                if df[item['col_name']].dtypes == object:
                    metric = dict(label=item['label'],
                                  tickvals=df[item["col_name"] + '_code'].unique(),
                                  ticktext=df[item['col_name']].unique(),
                                  values=df[item["col_name"] + '_code'])
                else:
                    metric = dict(label=item['label'], values=df[item['col_name']])
                pc_list.append(metric)
        dimensions = list(pc_list)
    else:
        dimensions = par_coord_data['data'][0]['dimensions']

    # Creates new figure.
    fig = go.Figure(
        layout=go.Layout(
            title=go.layout.Title(text="Scenario Pathways", font=dict(size=25, color='white')),
            height=600,  # px
        ),
        data=go.Parcoords(
            line=line,
            dimensions=dimensions,
        ),

    )
    fig.update_traces(labelangle=20, selector=dict(type='parcoords'))
    #fig.update_traces(labelfont_size=10, selector=dict(type='parcoords'))
    #fig.update_traces(rangefont_size=5, selector=dict(type='parcoords'))
    #fig.update_traces(tickfont_size=5, selector=dict(type='parcoords'))
    #fig.update_traces(tickfont_color='white', selector=dict(type='parcoords'))
    #fig.update_traces(line_colorbar_tickfont_size=100, selector=dict(type='parcoords'))
    #fig.update_traces(labelside='bottom', selector=dict(type='parcoords'))
    #fig.update_traces(line_colorbar_ticklabelposition='outside', selector=dict(type='parcoords'))
    #fig.update_traces(line_colorbar_tickformatstops=list(...), selector=dict(type='parcoords'))
    return fig

# This method filters the df based on the par_coords state variable of pc_chart id.. for example...
# State('pc-graph', 'figure')
def pc_chart_filter_df(df_filt, par_coord_data):
    # Skip if state does not exist. This will happen on initialization of graph.
    if par_coord_data != None and 'data' in par_coord_data:
        # Create Filter data based on PC dimension contraints.
        # Iterate through all dimensions in pc chart.
        for d in par_coord_data['data'][0]['dimensions']:
            # Determine if there are constraints on dimension.
            if 'constraintrange' in d:
                # Create mask dataframe for item that are selected.
                crs = np.array(d['constraintrange'])
                if crs.ndim == 1:
                    crs = [crs]
                masks = []
                for cr in crs:
                    key = {v: k for k, v in labels.items()}[d['label']]
                    # If a string coverted column, use the *_code version.
                    if df_filt[key].dtypes == object:
                        key = key + '_code'
                    masks.append(df_filt[key].between(*cr))
                # Apply mask to our cloned dataframe.
                df_filt = df_filt[np.logical_or.reduce(masks)]
    return df_filt

def get_scatter_graph(df_filt, xy_scatter_color_dropdown, xy_scatter_x_axis_dropdown, xy_scatter_y_axis_dropdown):
    scatter_graph = None
    # Create/Update standard scatter graph with filtered data.
    if df_filt.index.empty:
        # If empty, let user know and create blank figure.
        scatter_graph = px.scatter()
        scatter_graph.layout.annotations = [dict(text='filtering results in empty dataframe', showarrow=False)]
    else:
        scatter_graph = px.scatter(
            data_frame=df_filt,
            x=xy_scatter_x_axis_dropdown,
            y=xy_scatter_y_axis_dropdown,
            color=xy_scatter_color_dropdown,
            hover_data=['index', 'baseline_necb_tier', 'cost_equipment_total_cost_per_m_sq',
             'cost_utility_neb_total_cost_per_m_sq', 'baseline_savings_energy_cost_per_m_sq',
             'energy_eui_total_gj_per_m_sq', 'baseline_energy_percent_better', 'cost_utility_ghg_total_kg_per_m_sq',
             'baseline_ghg_percent_better', 'energy_peak_electric_w_per_m_sq', 'baseline_peak_electric_percent_better',
             ':building_type', ':template', ':primary_heating_fuel', ':rotation_degrees', ':scale_x', ':scale_y',
]

        #hover_data=[d['col_name'] for d in metrics if 'col_name' in d]
            #marginal_y="histogram",
            #marginal_x="histogram"
        )
    return scatter_graph

def get_scatter_graph_form_group():
    options = [
        {'label': d['label'], 'value': d['col_name']} for d in metrics
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

def get_data_table(id='data-table'):
    data_table = dash_table.DataTable(data=start_table_df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in start_table_df.columns],
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

    )
    return data_table

#### Main

# Load Sample data used by dash library.
df = load_dataframe()



# Create a hash from the metrics data so it can be easily used.
labels = {d['col_name']: d['label'] for d in metrics}

# Sort columns...not used?
labelsrev = {v: k for k, v in labels.items()}



# Set up app and use standard BOOTSTRAP theme.
app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)


# This is required due to a bug in the data_table. https://github.com/plotly/dash-table/issues/436
start_table_df = pd.DataFrame(columns=['Start Column'])
# Basic HTMl Bootstrap / Layout
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Design Contraints', children=[
        # PC Chart layout
        dbc.Row(
            dbc.Col(
                [
                    html.H3(children='Select Design Contraints'),
                    dcc.Graph(
                        id='pc-graph'
                    )
                ],
                align="center",
            )
        )]),
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
                            children=get_scatter_graph_form_group(),
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
                        get_data_table(id='data-table')
                    ],
                    md=12
                )
            ],
            align="center",
        )])])
    ],
    style={'padding': '20px 20px 20px 20px'} # Added in style padding to ignore the cutoffs
)


## Callback / Updates
@app.callback(
    Output('scatter-graph', 'figure'),
    Output('data-table', component_property='columns'),
    Output('data-table', component_property='data'),
    Output('data-table', component_property='style_cell_conditional'),
    Output('pc-graph', 'figure'),
    Input('pc-graph', 'restyleData'),  # Needed for event call.
    Input('xy_scatter_x_axis_dropdown', 'value'),
    Input('xy_scatter_y_axis_dropdown', 'value'),
    Input('xy_scatter_color_dropdown', 'value'),
    State('pc-graph', 'figure'),
)
def update_graphs(restyledata,
                  xy_scatter_x_axis_dropdown,
                  xy_scatter_y_axis_dropdown,
                  xy_scatter_color_dropdown,
                  par_coord_data
                  ):
    # Copy original dataframe.
    df_filt = df.copy()

    # Create/Update pc_chart from original df.
    pc_fig = get_pc_chart(df=df, par_coord_data=par_coord_data)

    # Filter copy of dataframe based on paracoords selections
    df_filt = pc_chart_filter_df(df_filt, par_coord_data)

    # Chart scatter plot with filtered dataframe.
    scatter_graph = get_scatter_graph(df_filt, xy_scatter_color_dropdown, xy_scatter_x_axis_dropdown,
                                      xy_scatter_y_axis_dropdown)

    return [
        scatter_graph,  # Scatter figure
        [
            {"name": i['label'], "id": i['col_name'], "deletable": True, "selectable": True, 'type':'text','presentation':'markdown'} for i in
            table_metrics
        ],  # data-table columns
        df_filt.to_dict('records'),  # data-table filtered data
        create_conditional_style(df_filt),  # col width based on column name.
        pc_fig  # pc-chart
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
