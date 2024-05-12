import dash_bootstrap_components as dbc
import dash_daq as daq
import dash
import stoch_LSP_PP
from dash import Dash, dcc, html, Output, Input, State, callback
from dash_iconify import DashIconify

a0 = [0.4]
an1 = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]
epsilons = {b:[round(b-i*0.05,2) for i in range(6)] if b < 0.975 else [b]+[round(b-0.025-i*0.05,2) for i in range(5)] for b in an1}
alpha = [(a,b) for a in a0 for b in an1 if a <= b]

data = "T20_S150_n4"

container_bg = "mediumturquoise"
header_bg = "#2DB5AF"; header_text_color="black"
border_color = "#269A94"; light_bg = "#ACEAE7"

dash.register_page(__name__, name="Time Period Service Level", order=2)

layout = html.Div([

    html.Div([html.H1("Time Period Service Level", style={"textAlign":"left", "margin-top":"5px"}, className="mx-4 px-2")]),
    
    dbc.Row([ # Graphs
        
        dcc.Tabs(children = [ 
            dcc.Tab([
                
                html.Div([
                    html.Div([html.Span(className="tab"),
                            strategy := dbc.Button("Switch to stat-dyn" , n_clicks=0, color="primary"),
                            ind_tab_title := html.H4("Static-static strategy Service Level analysis")
                            ], style={"backgroundColor":"white", "height":"3.5rem"}, className="hstack gap-5 d-flex align-items-center"),
                    
                    sl_analysis := dcc.Graph(figure = {}, mathjax=True, className="mx-0 px-0", style={"height":"700px"})
                    
                    ], className="vstack gap-0")

                ],label="Individual strategy analysis", value="ind", selected_style={"fontWeight":"bold"}),

            dcc.Tab([
                
                html.Div([

                    html.Div([
                            dbc.Col([], width=1, style={"margin-top":"20px"}),
                            dbc.Col([scale_check := dcc.Checklist(options=[{"label":"Scale y axis", "value":"scale"}], value=["scale"])], width=11)
                            ], style={"height":"3.5rem"}, className="hstack gap-0 w-100 bg-white"),

                    html.Div([

                        html.Div([
                            html.Div(["Select the chart to display"], style={"fontWeight":"bold", "font-size":20, "height":"2rem"}, className="px-3 py-3"),
                            chart_radio := dcc.RadioItems([
                                {"label":html.Div(["Total expected cost"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"tot_cost"},
                                {"label":html.Div(["Proportion of production days"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"setup"},
                                {"label":html.Div(["Average capacity utilization"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"lot_size"},
                                {"label":html.Div(["Production cost"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"prod_cost"},
                                {"label":html.Div(["Holding cost"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"hold_cost"},
                                {"label":html.Div(["Fresh produce fill rate"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"fresh_fr"},
                                {"label":html.Div(["Overall fill rate"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"over_fr"},
                                {"label":html.Div(["Waste level (/prod.)"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"w_prod"},
                                {"label":html.Div(["Waste level (/dem.)"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px", "margin-bottom":"3px"}), "value":"w_dem"}
                                ], value="tot_cost", style={"width":"100%"}, className="px-3")
                            ], style={"margin":"15px"}, className="vstack gap-4 border rounded w-25 h-50 bg-white"),

                        html.Div([comb_sl := dcc.Graph(figure={}, mathjax=True)], className="w-75")
                        
                        ], style={"height":"700px"}, className="hstack gap-0 w-100 bg-white align-items-baseline"),
                    
                    ], className="vstack gap-0 w-100")
                
                ], label="Strategies comparison analysis", value="comb", selected_style={"fontWeight":"bold"})
            
            ], value="ind")
        
        ], justify="center", align="center", style={"width":"100%", "backgroundColor":container_bg, "margin-top":"10px"}),
    
    html.Div([ # Filters panel

        filter := dbc.Button([DashIconify(icon="mingcute:filter-line", width=35, color="black")], n_clicks=0, style={"backgroundColor":"silver", "border-radius":"50%", "height":"60px", "width":"60px"}, className="border-0"),
        side_filter := dbc.Offcanvas([html.Div([

                dbc.Card(html.Div([

                    dcc.Markdown(r"$\alpha_{n-1}$", mathjax=True, style={"textAlign":"center", "height":"1.5rem", "width":"58px"}),
                    alphan1_range := dcc.RangeSlider(min=an1[0], max=an1[-1], marks={b:{"label":f"{b:.1%}", "style":{"color":"black"}} for b in an1}, value=[an1[0],an1[-1]], allowCross=False, step=None)
                
                ], style={"display":"grid", "grid-template-columns":"5% 95%"}, className="align-items-center"), style={"borderColor":border_color})
                

            ], className="vstack gap-3")], title="Data filters", placement="bottom", scrollable=True, is_open=False, style={"backgroundColor":light_bg})

    ], style={"position":"sticky", "bottom":"80px", "start":"10px"}),

    html.Div([ # Visualization options panel

        settings := dbc.Button([DashIconify(icon="healthicons:ui-preferences", width=35, color="black")], n_clicks=0, style={"backgroundColor":"silver", "border-radius":"50%", "height":"60px", "width":"60px"}, className="border-0"),
        side_settings := dbc.Offcanvas([html.Div([
                
                dbc.Card([html.Div([
                    html.Div("View by", style={"textAlign":"center", "color":"black", "height":"1.5rem"}, className="my-1"),

                    html.Hr(style={"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}),

                    html.Div([
                        dcc.Markdown(r"$\beta$", mathjax=True, style={"textAlign":"right", "color":"black", "height":"1.5rem", "width":"58px"}),
                        view_switch := daq.ToggleSwitch(value=True, color=header_bg, style={"width":"59px"}),
                        dcc.Markdown(r"$\alpha_{n-1}$", mathjax=True, style={"textAlign":"left", "color":"black", "height":"1.5rem", "width":"58px"})

                    ], className="hstack gap-2 my-1")

                ], className="vstack gap-0")], style={"width":"175px", "borderColor":border_color}),

                dbc.Card([html.Div([
                    html.Div("Hover mode", style={"textAlign":"center", "color":"black", "height":"1.5rem"}, className="my-1"),

                    html.Hr(style={"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}),

                    html.Div([
                        dcc.Markdown(r"Closest", mathjax=True, style={"textAlign":"right", "color":"black", "height":"1.5rem", "width":"66px"}),
                        hover_switch := daq.ToggleSwitch(value=False, color=header_bg, style={"width":"67px"}),
                        dcc.Markdown(r"Unified", mathjax=True, style={"textAlign":"left", "color":"black", "height":"1.5rem", "width":"67px"})

                    ], className="hstack gap-2 my-1")
                
                ], className="vstack gap-0")], style={"width":"200px", "borderColor":border_color})

        ], className="hstack gap-5")], title="Visualization options", placement="bottom", scrollable=True, is_open=False, style={"backgroundColor":light_bg})

    ], style={"position":"sticky", "bottom":"10px", "start":"10px"})

])

@callback(
    Output(sl_analysis, component_property="figure"),
    Output(comb_sl, component_property="figure"),
    Output(strategy, component_property="children"),
    Output(ind_tab_title, component_property="children"),
    Input(view_switch, component_property="value"),
    Input(hover_switch, component_property="value"),
    Input(alphan1_range, component_property="value"),
    Input(strategy, component_property="n_clicks"),
    Input(chart_radio, component_property="value"),
    Input(scale_check, component_property="value")
)
def update_layout(view_bool, hover_bool, range_n1, m, plot_radio, scale_y):
    
    b0, bn1 = stoch_LSP_PP.data_mgmt.filter_data_tp(an1, range_n1); reps = list(range(5))
    tot_fr = [(b,e) for b in bn1 for e in epsilons[b]]
    diff_epsilons = list(set([e for (b,e) in tot_fr])); diff_epsilons.sort()

    if m % 2 == 0: st = "stat"; but = "Switch to stat-dyn"; tit = "Static-static strategy Service Level analysis"
    else: st = "dyn"; but= "Switch to stat-stat"; tit = "Static-dynamic strategy Service Level analysis"

    fig1 = stoch_LSP_PP.charts.gen_ind_tp_sl_analysis(data, 2, tot_fr, bn1, epsilons, diff_epsilons, reps, st, view_bool, hover_bool)
    fig2 = stoch_LSP_PP.charts.gen_comb_sl_analysis(data, 1, alpha, b0, bn1, reps, view_bool, hover_bool, plot_radio, scale_y)
    
    return fig1, fig2, but, tit

@callback(
    Output(side_settings, component_property="is_open"),
    Input(settings, component_property="n_clicks"),
    State(side_settings, component_property="is_open"),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

@callback(
    Output(side_filter, component_property="is_open"),
    Input(filter, component_property="n_clicks"),
    State(side_filter, component_property="is_open"),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open