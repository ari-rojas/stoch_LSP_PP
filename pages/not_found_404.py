import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Dash, dcc, html, Output, Input, callback
import dash
import stoch_LSP_PP

dash.register_page(__name__, name="Home", order=0)

layout = html.Div([

    html.H1("Home", style={"textAlign":"left", "margin-top":"5px"}, className="mx-4 px-2")

    ])
