from dash import Dash, dcc, html, Output, Input
import dash_bootstrap_components as dbc

app = Dash(__name__, extra_hot_reload_paths=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([output := dcc.Markdown(children=""),
                            text := dcc.Input(value="Type text here")])

@app.callback(
    Output(output, component_property="children"),
    Input(text, component_property="value")
)
def update_graph(texto):
    return texto

if __name__ == "__main__":
    app.run_server(debug=True)
