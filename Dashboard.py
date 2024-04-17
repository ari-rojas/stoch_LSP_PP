import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash_daq as daq

from dash import Dash, dcc, html, Output, Input
from plotly.express.colors import sample_colorscale
from plotly.subplots import make_subplots
from pickle import load, dump

a0 = [0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]
an1 = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]

container_bg = "mediumturquoise"
header_bg = "#2DB5AF"; header_text_color="black"
border_color = "#269A94"
light_bg = "#ACEAE7"

def import_data(experiment, tab, alpha):

    file = open(f"./Experiments/Parameters/Global_{experiment}", "rb")
    (T, S, G, n, h, c, f, C) = load(file); file.close()

    setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem = dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict()
    for (a,b) in alpha:
        file = open(f"./Experiments/Performance metrics/Age_service_level_{a,b}_stat-{tab}", "rb")
        (setup[a,b], holding[a,b], production[a,b], total[a,b], period_sl[a,b], total_sl[a,b], waste_prod[a,b], waste_dem[a,b]) = load(file); file.close()

    return (T, S, G, n, h, c, f, C), (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem)

def process_data(S, metrics, reps, alpha):

    metrics = list(metrics)

    for m in metrics:
        for (a,b) in alpha:
            for rep in reps:

                if isinstance(m[a,b][rep], list):
                    m[a,b][rep] = sum(m[a,b][rep])/len(S)
    
    return tuple(metrics)


def filter_data(a0, vals0, an1, valsn1):

    b0 = [a for a in a0 if a >= vals0[0] and a <= vals0[1]]
    bn1 = [b for b in an1 if b >= valsn1[0] and b <= valsn1[1]]

    return b0, bn1

def plot_service_level_analysis(b0, bn1, reps, S, G, f, c, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, tab):

    if tab == "stat": s1 = "Average lot size"; s2 = "Production cost"
    else: s1 = "Expected average lot size"; s2 = "Expected production cost"

    fig = make_subplots(rows=2, cols=5, horizontal_spacing=0.05, vertical_spacing=0.15, subplot_titles=["Total expected cost","Setup operations",s1,s2,"Expected holding cost",
                                                    "Achieved fresh produce fill rate","Achieved overall fill rate","Waste level (/prod.)","Waste level (/dem.)",None])

    
    if view_bool:
        cols = sample_colorscale("plasma",[(bn1[-1]-b)/(bn1[-1]-bn1[0]) for b in bn1])
        y_axis_container = bn1; x_axis_container = b0
        hover_text = "α(0)"; x_ax_title = r"$\alpha_0$"; legend_title = r"$\alpha_{n-1}$"

        fresh_prod_sl = {"ticks":"outside", "ticktext":[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in b0]}
        total_prod_sl = {"ticks":"", "ticktext":[f"{b:.0%}" for b in bn1]}
    else:
        cols = sample_colorscale("turbo",[(a-b0[0])/(b0[-1]-b0[0]) for a in b0])
        y_axis_container = b0; x_axis_container = bn1
        hover_text = "α(n-1)"; x_ax_title = r"$\alpha_{n-1}$"; legend_title = r"$\alpha_0$"

        fresh_prod_sl = {"ticks":"", "ticktext":[f"{a:.0%}" for a in b0]}
        total_prod_sl = {"ticks":"outside", "ticktext":[f"{b:.0%}" if b*100 % 10 == 0 else "" for b in bn1]}

    ix=0
    for b in y_axis_container:
        if view_bool: xpoints = [a for a in x_axis_container if a <= b]; comb = {a:(a,b) for a in xpoints}
        else: xpoints = [a for a in x_axis_container if a >= b]; comb = {a:(b,a) for a in xpoints}

        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([setup[comb[a]][rep]/f for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Setups = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production[comb[a]][rep]*f/(setup[comb[a]][rep]*c) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Avg. Lot Size = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=3)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=4)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([holding[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=5)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl[comb[a]][rep][0] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Fresh produce fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl[comb[a]][rep][G[-1]] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Overall fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=2, col=2)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_prod[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=2, col=3)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_dem[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br> Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=True), row=2, col=4)
        ix += 1

    for i in range(1,6):
        fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_container, ticktext=[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in x_axis_container], showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
    for i in range(1,5):
        fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_container, ticktext=[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in x_axis_container], showline=True, linewidth=1, linecolor="black", row=2, col=i, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=b0, ticks=fresh_prod_sl["ticks"], ticktext=fresh_prod_sl["ticktext"], row=2, col=1, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=bn1, ticks=total_prod_sl["ticks"], ticktext=total_prod_sl["ticktext"], row=2, col=2, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=3, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=4, tickfont={"color":"black"})

    fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":40}, legend={"x":0.875, "y":0, "xref":"paper", "yref":"paper", "itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16}}, height=700)
    fig.update_layout(shapes=[dict(type="line", xref='paper', yref='paper', x0=-0.1, y0=0.475, x1=1.1, y1=0.475, line=dict(color="black", width=1))], hovermode="x" if hover_bool else "closest")
    fig.update_annotations(font_color="black")

    return fig


app = Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP], assets_external_path="./assets/")

app.layout = dbc.Container([
    
    dbc.Row([ # Title and data input selection

        dbc.CardGroup([
            
            dbc.Card([dbc.CardBody([

                    dcc.Markdown("", style={"textAlign":"center"})
                ])], color=light_bg, style={"borderColor":border_color}),

            dbc.Card([dbc.CardBody([

                    dcc.Markdown("#### Stochastic Lot Sizing Problem for Perishable Products\n"+
                                    "###### Ariel Rojas\n", style={"textAlign":"center", "color":"black"})
                ])], color=light_bg, style={"borderColor":border_color}),
            
            dbc.Card([dbc.CardBody([
                    dbc.Row([html.H6("Select Experimental Setup")]),
                    dbc.Row([data_input := dcc.Dropdown(options=[{"label":"T = 20, S = 150, n = 4 (5)", "value":"T20_S150_n4"}], value="T20_S150_n4",  style={"borderColor":"#269A94"})]),
                    dbc.Row([
                        
                        dbc.Col([], width=2),

                        dbc.Col([
                            html.Small([html.Small("T: time periods"),html.Br(),html.Small("S: scenarios")])
                            ], width=4),
                        
                        dbc.Col([
                            html.Small([html.Small("n: shelf life of product"),html.Br(),html.Small("(-): number of replicas")])
                            ], width=4),

                        dbc.Col([], width=2)
                        
                        ])
                    
                ], className="my-0 py-2")], color=light_bg, style={"borderColor":border_color}, className="w-50"),
        
            ], style={"margin-top":"10px"})

        ], justify="center", align="center", style={"width":"100%", "backgroundColor":container_bg}),
    
    dbc.Row([ # Data visual settings and filtering
        
        dbc.Col([dbc.Card([ # Data visualization settings

            dbc.CardHeader("Settings", style={"textAlign":"center", "color":header_text_color, "backgroundColor":light_bg, "borderColor":border_color}),

            dbc.CardBody([
                
                dbc.Row([
                    html.Div("View by", style={"textAlign":"center", "color":"black"})
                    ]),
                    
                dbc.Row([
                    dbc.Col([
                        dcc.Markdown(r"$\alpha_0$", mathjax=True, style={"textAlign":"right", "color":"black", "height":"1.5rem"})
                        ]),

                    dbc.Col([
                        view_switch := daq.ToggleSwitch(value=True, color=header_bg)
                        ]),
                    
                    dbc.Col([
                        dcc.Markdown(r"$\alpha_{n-1}$", mathjax=True, style={"textAlign":"left", "color":"black", "height":"1.5rem"})
                        ]),

                    ], justify="center", align="center"),
            
                dbc.Row([
                    html.Div("Hover mode", style={"textAlign":"center", "height":"1.5rem", "color":"black"})
                    ]),

                dbc.Row([
                    dbc.Col([
                        html.Div("Closest", style={"textAlign":"right", "height":"1.5rem", "color":"black"})
                        ], className="mx-0 px-0"),
                    
                    dbc.Col([
                        hover_switch := daq.ToggleSwitch(value=False, color=header_bg)
                        ], className="mx-0 px-0"),

                    dbc.Col([
                        html.Div("Unified", style={"textAlign":"left", "height":"1.5rem", "color":"black"})
                        ], className="mx-0 px-0")
                    
                    ], justify="center", align="center")


                ], className="my-0 py-1"), 
            
            ], style={"borderColor":border_color})], width = 2, style={"margin-top":"10px"}),

        dbc.Col([dbc.Card([ # Data filtering

            dbc.CardHeader("Filters", style={"textAlign":"center", "color":header_text_color, "backgroundColor":light_bg, "border_color":border_color}),

            dbc.CardBody([

                dbc.Row([

                    dbc.Col([
                        dcc.Markdown(r"$\alpha_0$", mathjax=True, style={"textAlign":"right", "height":"1.5rem"})
                        ], width=1, className="mx-0 px-0"),

                    dbc.Col([
                        alpha0_range := dcc.RangeSlider(min=a0[0], max=a0[-1], marks={a:{"label":f"{a:.1%}", "style":{"color":"black"}} for a in a0}, value=[a0[0],a0[-1]], allowCross=False, step=None)
                        ], width=11, className="mx-0 px-0")
                    ]),
                
                dbc.Row([

                    dbc.Col([
                        dcc.Markdown(r"$\alpha_{n-1}$", mathjax=True,  style={"textAlign":"right", "height":"1.5rem"})
                        ], width=1, className="mx-0 px-0"),
                    
                    dbc.Col([
                        alphan1_range := dcc.RangeSlider(min=an1[0], max=an1[-1], marks={b:{"label":f"{b:.1%}", "style":{"color":"black"}} for b in an1}, value=[an1[0],an1[-1]], allowCross=False, step=None)
                        ], width=11, className="mx-0 px-0")
                    ])

                ], className="my-0 py-1")
            
            ], style={"borderColor":border_color})], width = 10, style={"margin-top":"10px"})

        ], justify="center", align="center", style={"width":"100%", "backgroundColor":container_bg}),
    
    dbc.Row([ # Graphs
        
        graphs_tabs := dcc.Tabs( value="stat", children = [ 
            dcc.Tab(label="Static-static", value="stat", selected_style={"fontWeight":"bold"}),
            dcc.Tab(label="Static-dynamic", value="dyn", selected_style={"fontWeight":"bold"})
            ]),
        
        sl_analysis := dcc.Graph(figure={}, mathjax=True)
        
        ], justify="center", align="center", style={"width":"100%", "backgroundColor":container_bg, "margin-top":"10px"})

], fluid=True, style={"backgroundColor":container_bg})

@app.callback(
    Output(sl_analysis, component_property="figure"),
    Input(data_input, component_property="value"),
    Input(view_switch, component_property="value"),
    Input(hover_switch, component_property="value"),
    Input(alpha0_range, component_property="value"),
    Input(alphan1_range, component_property="value"),
    Input(graphs_tabs, component_property="value")
)
def update_graph(data, view_bool, hover_bool, range_0, range_n1, tab):

    alpha = [(a,b) for a in a0 for b in an1 if a <= b]
    b0, bn1 = filter_data(a0, range_0, an1, range_n1)
    reps = list(range(5))

    (T, S, G, n, h, c, f, C), metrics = import_data(data, tab, alpha)
    (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem) = process_data(S, metrics, reps, alpha); del metrics

    fig = plot_service_level_analysis(b0, bn1, reps, S, G, f, c, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, tab)

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
