"""
Note that the callback will trigger even if prevent_initial_call=True. This is because dcc.Location must
be in app.py.  Since the dcc.Location component is not in the layout when navigating to this page, it triggers the callback.
The workaround is to check if the input value is None.

"""
from dash import dcc, html, Input, Output, callback, register_page
import dash_bootstrap_components as dbc

import plotly.express as px

# Etc
import pandas as pd
import arrow

# e-mission modules
import emission.core.get_database as edb

from opadmindash.permissions import has_permission

register_page(__name__, path="/")


def compute_sign_up_trend(uuid_df):
    uuid_df['update_ts'] = pd.to_datetime(uuid_df['update_ts'])
    res_df = (
        uuid_df
            .groupby(uuid_df['update_ts'].dt.date)
            .size()
            .reset_index(name='count')
            .rename(columns={'update_ts': 'date'})
        )
    res_df['date'] = pd.to_datetime(res_df['date'])
    return res_df


def compute_trips_trend(trips_df, date_col):
    trips_df[date_col] = pd.to_datetime(trips_df[date_col], utc=True)
    trips_df[date_col] = pd.DatetimeIndex(trips_df[date_col]).date
    counts = (trips_df
        .groupby(date_col)
        .size()
        .reset_index(name='count')
        .rename(columns={date_col: 'date'})
    )
    return counts

def find_last_get(uuid):
    last_get_result_list = list(edb.get_timeseries_db().find({"user_id": uuid,
        "metadata.key": "stats/server_api_time",
        "data.name": "POST_/usercache/get"}).sort("data.ts", -1).limit(1))
    last_get = last_get_result_list[0] if len(last_get_result_list) > 0 else None
    return last_get

def get_number_of_active_users(uuid_list, threshold):
    last_get_entries = [find_last_get(npu) for npu in uuid_list]
    number_of_active_users = 0
    for uuid, lge in zip(uuid_list, last_get_entries):
        if lge is not None:
            last_call_diff = arrow.get().timestamp - lge["metadata"]["write_ts"]
            if last_call_diff <= threshold:
                number_of_active_users += 1
    return number_of_active_users

intro = """
## Home
"""

card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": 30,
    "margin": "auto",
}

@callback(
    Output('card-users', 'children'),
    Input('store-uuids', 'data'),
)
def update_card_users(store_uuids):
    number_of_users = pd.DataFrame(store_uuids.get('data')).shape[0] if has_permission('overview_users') else 0
    card = generate_card("# Users", f"{number_of_users} users", "fa fa-users")
    return card

@callback(
    Output('card-active-users', 'children'),
    Input('store-uuids', 'data'),
)
def update_card_active_users(store_uuids):
    uuid_df = pd.DataFrame(store_uuids.get('data'))
    number_of_active_users = 0
    if not uuid_df.empty and has_permission('overview_active_users'):
        ONE_DAY = 100 * 24 * 60 * 60
        number_of_active_users = get_number_of_active_users(uuid_df['user_id'], ONE_DAY)
    card = generate_card("# Active users", f"{number_of_active_users} users", "fa fa-person-walking")
    return card

@callback(
    Output('card-trips', 'children'),
    Input('store-trips', 'data'),
)
def update_card_trips(store_trips):
    number_of_trips = pd.DataFrame(store_trips.get('data')).shape[0] if has_permission('overview_trips') else 0
    card = generate_card("# Confirmed trips", f"{number_of_trips} trips", "fa fa-angles-right")
    return card

def generate_card(title_text, body_text, icon): 
    card = dbc.CardGroup([
            dbc.Card(
                dbc.CardBody(
                    [
                            html.H5(title_text, className="card-title"),
                            html.P(body_text, className="card-text",),
                        ]
                    )
                ),
                dbc.Card(
                    html.Div(className=icon, style=card_icon),
                    className="bg-primary",
                    style={"maxWidth": 75},
                ),
            ])
    return card

def generate_barplot(data, x, y, title):
    fig = px.bar()
    if data is not None:
        fig = px.bar(data, x=x, y=y)
    fig.update_layout(title=title)
    return fig


@callback(
    Output('fig-sign-up-trend', 'figure'),
    Input('store-uuids', 'data'),
)
def generate_plot_sign_up_trend(store_uuids):
    df = pd.DataFrame(store_uuids.get("data"))
    trend_df = None
    if not df.empty and has_permission('overview_signup_trends'):
        trend_df = compute_sign_up_trend(df)
    fig = generate_barplot(trend_df, x = 'date', y = 'count', title = "Sign-ups trend")
    return fig

@callback(
    Output('fig-trips-trend', 'figure'),
    Input('store-trips', 'data'),
)
def generate_plot_trips_trend(store_trips):
    df = pd.DataFrame(store_trips.get("data"))
    trend_df = None
    if not df.empty and has_permission('overview_trips_trend'):
        trend_df = compute_trips_trend(df, date_col = "trip_start_time_str")
    fig = generate_barplot(trend_df, x = 'date', y = 'count', title = "Trips trend")
    return fig


layout = html.Div(
    [
        dcc.Markdown(intro),

        # Cards 
        dbc.Row([
            dbc.Col(id='card-users'),
            dbc.Col(id='card-active-users'),
            dbc.Col(id='card-trips')
        ]),

        # Plots
        dbc.Row([
            dcc.Graph(id="fig-sign-up-trend"),
            dcc.Graph(id="fig-trips-trend"),
        ])
    ]
)
