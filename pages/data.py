"""
Note that the callback will trigger even if prevent_initial_call=True. This is because dcc.Location must be in app.py.
Since the dcc.Location component is not in the layout when navigating to this page, it triggers the callback.
The workaround is to check if the input value is None.
"""
from dash import dcc, html, Input, Output, callback, register_page
import dash_table

# Etc
import pandas as pd
from dash.exceptions import PreventUpdate

from opadmindash.permissions import has_permission, get_trips_columns

register_page(__name__, path="/data")

intro = """
## Data
"""

layout = html.Div(
    [   
        dcc.Markdown(intro),
        dcc.Tabs(id="tabs-datatable", value='tab-uuids-datatable', children=[
            # dcc.Tab(label='Demographics survey', value='tab-demographics-survey-datatable'),
            dcc.Tab(label='UUIDs', value='tab-uuids-datatable'),
            dcc.Tab(label='Trips', value='tab-trips-datatable'),
        ]),
        html.Div(id='tabs-content'),
    ]
)


@callback(
    Output('tabs-content', 'children'),
    Input('tabs-datatable', 'value'),
    Input('store-uuids', 'data'),
    Input('store-trips', 'data'),
)
def render_content(tab, store_uuids, store_trips):
    if tab == 'tab-uuids-datatable':
        df = pd.DataFrame(store_uuids["data"])
        if df.empty or not has_permission('data_uuids'):
            return None
        return populate_datatable(df)
    elif tab == 'tab-trips-datatable':
        df = pd.DataFrame(store_trips["data"])
        if df.empty or not has_permission('data_trips'):
            return None
        if 'data.start_loc' in get_trips_columns():
            df['start_coordinates'] = df['start_coordinates'].apply(lambda x: f'({x[0]}, {x[1]})')
        else:
            df = df.drop(columns=['start_coordinates'])
        if 'data.end_loc' in get_trips_columns():
            df['end_coordinates'] = df['end_coordinates'].apply(lambda x: f'({x[0]}, {x[1]})')
        else:
            df = df.drop(columns=['end_coordinates'])

        return populate_datatable(df)


def populate_datatable(df):
    if not isinstance(df, pd.DataFrame):
        raise PreventUpdate
    return dash_table.DataTable(
        # id='my-table',
        # columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        export_format="csv",
        filter_options={"case": "sensitive"},
        # filter_action="native",
        sort_action="native",  # give user capability to sort columns
        sort_mode="single",  # sort across 'multi' or 'single' columns
        page_current=0,  # page number that user is on
        page_size=50,  # number of rows visible per page
        style_cell={
            'textAlign': 'left',
            # 'minWidth': '100px',
            # 'width': '100px',
            # 'maxWidth': '100px',
        },
        style_table={'overflowX': 'auto'}
    )
