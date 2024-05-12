import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Dash, dcc, html, Output, Input, State
from dash_iconify import DashIconify
import dash

a0 = [0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]
an1 = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]
alpha = [(a,b) for a in a0 for b in an1 if a <= b]

container_bg = "mediumturquoise"
header_bg = "#2DB5AF"; header_text_color="black"
border_color = "#269A94"; light_bg = "#ACEAE7"

app = Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP], assets_external_path="./assets/", use_pages=True, suppress_callback_exceptions=True)

app.layout = dbc.Container([
    
    html.Div([

        html.Div([

            menu := dbc.Button([DashIconify(icon="material-symbols:menu", width=40, color="black")], n_clicks=0, className="bg-transparent border-0 rounded-0"),
            side_menu := dbc.Offcanvas(
                [html.Div(dcc.Link(f"{page['name']}", href=page["relative_path"])) for page in dash.page_registry.values()]
            , title="Page explorer", is_open=False)

        ], className="mx-3"),
        
        html.Div([
            html.H4("Stochastic Lot Sizing Problem for Perishable Products", style={"textAlign":"center", "margin-bottom":"2"}),
            html.H6("Ariel Rojas", style={"textAlign":"center", "margin-bottom":"0"})
        ], className="vstack gap-0")

    ], className="hstack gap-3 w-100 py-3"),

    dash.page_container

], fluid=True, style={"backgroundColor":container_bg})

@app.callback(
    Output(side_menu, component_property="is_open"),
    Input(menu, component_property="n_clicks"),
    State(side_menu, component_property="is_open"),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

if __name__ == "__main__":
    app.run(debug=True)
