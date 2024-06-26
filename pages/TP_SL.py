import dash_bootstrap_components as dbc
import dash_daq as daq
import dash
import stoch_LSP_PP
from dash import Dash, dcc, html, Output, Input, State, callback, no_update, ctx
from dash_iconify import DashIconify

betas = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]
an1 = [0.8, 0.85, 0.9, 0.95, 0.975]
tot_fr = [(beta,b) for beta in betas for b in an1 if beta <= b]
page = 2; reps = list(range(5)); sl_type = "lit"

data = "T30_S150_n4"

container_bg = "mediumturquoise"
header_bg = "#2DB5AF"; header_text_color="black"
border_color = "#269A94"; light_bg = "#ACEAE7"

dash.register_page(__name__, name="Time Period Service Level", order=2)

layout = html.Div([

    html.Div([html.H1("Time period service level requirement", style={"textAlign":"left", "margin-top":"5px"}, className="mx-4 px-2")]),
    
    dbc.Row([ # Graphs
        
        dcc.Tabs(children = [ 
            dcc.Tab([
                
                html.Div([
                    html.Div([html.Span(className="tab"),
                            strategy := dbc.Button("Switch to stat-dyn" , n_clicks=0, color="primary"),
                            sl_button := dbc.Button("Switch to lit-sl" , n_clicks=0, color="primary"),
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
                                {"label":html.Div(["Production cost"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"prod_cost"},
                                {"label":html.Div(["Holding cost"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"hold_cost"},
                                {"label":html.Div(["Fresh produce fill rate"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"fresh_fr"},
                                {"label":html.Div(["Overall fill rate"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"over_fr"},
                                {"label":html.Div(["Proportion of production days"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"setup"},
                                {"label":html.Div(["Average capacity utilization"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"lot_size"},
                                {"label":html.Div(["Waste level (/prod.)"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px"}), "value":"w_prod"},
                                {"label":html.Div(["Waste level (/dem.)"], style = {"color":"black", "display":"inline-block", "margin-top":"3px", "margin-left":"10px", "margin-bottom":"3px"}), "value":"w_dem"}
                                ], value="tot_cost", style={"width":"100%"}, className="px-3"),

                            html.Div(download_btn := dbc.Button("Download plot", id="download_btn", style={"backgroundColor":header_bg}, className="border-0"), style={"textAlign":"center", "margin":"auto"}, className="w-50")
                            
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

                    dcc.Markdown(r"$\beta$", mathjax=True, style={"textAlign":"center", "height":"1.5rem", "width":"58px"}),
                    alpha0_range := dcc.RangeSlider(min=betas[0], max=betas[-1], marks={a:{"label":f"{a:.1%}", "style":{"color":"black"}} for a in betas}, value=[betas[0],betas[-1]], allowCross=False, step=None)
                
                ], style={"display":"grid", "grid-template-columns":"5% 95%"}, className="align-items-center"), style={"borderColor":border_color}),

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
                    npoints_text := html.Div("Number of points", style={"textAlign":"center", "color":"black", "height":"1.5rem"}, className="my-1"),

                    npoints_line := html.Hr(style={"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}),

                    html.Div([
                        npoints_mode := dcc.RadioItems(options=[
                            {"label":html.Div("All", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"a"},
                            {"label":html.Div("Last", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"l"}
                        ], value="a", style={"display":"flex"}),

                        npoints_last := dcc.Input(type="number", value=8, min=1, max=8, step=1, disabled=True, style={"color":"black"})

                    ], className="hstack my-1 px-3")
                
                ], className="vstack gap-0")], style={"width":"200px", "borderColor":border_color}),

                dbc.Card([html.Div([
                    relative_text := html.Div("Display values as", style={"textAlign":"center", "color":"black", "height":"1.5rem"}, className="my-1"),

                    relative_line := html.Hr(style={"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}),

                    html.Div([
                        relative_mode := dcc.RadioItems(options=[
                            {"label":html.Div("Absolute", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"abs"},
                            {"label":html.Div("Relative to", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"rel"}
                        ], value="abs", style={"display":"flex"}),

                        relative_last := dcc.Dropdown(options=[{"label":html.Div(f"{a:.0%}", style={"color":"black"}), "value":a} for a in betas if a <= 0.7], value=0.4, style={"color":"black", "width":"90px"}, disabled=True)

                    ], className="hstack my-1 px-3")
                
                ], className="vstack gap-0")], style={"width":"315px", "borderColor":border_color}),

                dbc.Card([html.Div([
                    xaxis_text := html.Div("Independent variable", style={"textAlign":"center", "color":"black", "height":"1.5rem"}, className="my-1"),

                    xaxis_line := html.Hr(style={"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}),
                    
                    html.Div([
                        x_axis_a0 := dcc.Markdown(r"$\beta$", mathjax=True, style={"textAlign":"right", "color":"black", "height":"1.5rem", "width":"48px"}),
                        xaxis_switch := daq.ToggleSwitch(value=False, color=header_bg, disabled=False, style={"width":"59px"}),
                        x_axis_an1a0 := dcc.Markdown(r"$\alpha_{n-1}-\beta$", mathjax=True, style={"textAlign":"left", "color":"black", "height":"1.5rem", "width":"103px"})
                    ], className="hstack gap-2 my-1")
                
                ], className="vstack gap-0")], style={"width":"210px", "borderColor":border_color}),

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
    Output(sl_button, component_property="children"),
    Output(ind_tab_title, component_property="children"),
    Input(view_switch, component_property="value"),
    Input(hover_switch, component_property="value"),
    Input(alpha0_range, component_property="value"),
    Input(alphan1_range, component_property="value"),
    Input(strategy, component_property="n_clicks"),
    Input(sl_button, component_property="n_clicks"),
    Input(chart_radio, component_property="value"),
    Input(scale_check, component_property="value"),
    Input(npoints_mode, component_property="value"),
    Input(npoints_last, component_property="value"),
    Input(xaxis_switch, component_property="value"),
    Input(download_btn, component_property="n_clicks"),
    Input(relative_mode, component_property="value"),
    Input(relative_last, component_property="value")
)
def update_layout(view_bool, hover_bool, range_beta, range_n1, m, sl_n, plot_radio, scale_y, np_mode, np_last, xaxis_bool, n_download, rel_mode, rel_last):
    
    filt_beta, bn1 = stoch_LSP_PP.data_mgmt.filter_data(betas, range_beta, an1, range_n1)
    st, but, tit = stoch_LSP_PP.charts.get_tabs_titles(m)
    sl_but, sl_type = ("Switch to lit-sl","base") if sl_n % 2 == 0 else ("Switch to scn-sl","lit")
    download = True if ctx.triggered_id == "download_btn" else False
    
    specifics = stoch_LSP_PP.charts.generate_plot_specifics(page, view_bool, np_mode, np_last, xaxis_bool, filt_beta, bn1)
    if rel_mode == "abs":
        fig1 = stoch_LSP_PP.charts.gen_ind_sl_analysis(data, page, tot_fr, filt_beta, bn1, reps, st, sl_type, view_bool, hover_bool, specifics, xaxis_bool)
        fig2 = stoch_LSP_PP.charts.gen_comb_sl_analysis(data, page, tot_fr, filt_beta, bn1, reps, sl_type, view_bool, hover_bool, plot_radio, scale_y, specifics, xaxis_bool, download)
    else:
        fig1 = stoch_LSP_PP.charts.gen_ind_sl_analysis_relative(data, page, tot_fr, filt_beta, bn1, reps, st, sl_type, view_bool, hover_bool, specifics, xaxis_bool, rel_last)
        fig2 = stoch_LSP_PP.charts.gen_comb_sl_analysis_relative(data, page, tot_fr, filt_beta, bn1, reps, sl_type, view_bool, hover_bool, plot_radio, scale_y, specifics, xaxis_bool, rel_last, download)
    
    return fig1, fig2, but, sl_but, tit


@callback(
    Output(side_settings, component_property="is_open"),
    Input(settings, component_property="n_clicks"),
    State(side_settings, component_property="is_open")
)
def toggle_offcanvas_settings(n1, is_open):
    if n1:
        return not is_open
    return is_open

@callback(
    Output(npoints_text, component_property="style"),
    Output(npoints_line, component_property="style"),
    Output(npoints_mode, component_property="value"),
    Output(npoints_mode, component_property="options"),
    Output(npoints_last, component_property="style"),
    Output(xaxis_text, component_property="style"),
    Output(xaxis_line, component_property="style"),
    Output(xaxis_switch, component_property="disabled"),
    Output(xaxis_switch, component_property="value"),
    Output(x_axis_a0, component_property="style"),
    Output(x_axis_an1a0, component_property="style"),
    Output(relative_text, component_property="style"),
    Output(relative_line, component_property="style"),
    Output(relative_mode, component_property="value"),
    Output(relative_mode, component_property="options"),
    Output(relative_last, component_property="options"),
    Input(view_switch, component_property="value")
)
def alpha0_disabling(view_bool):

    if view_bool:
        text_style = {"textAlign":"center", "color":"black", "height":"1.5rem"}
        line_style = {"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}
        mode = no_update; last_style = {"color":"black"}
        options = [{"label":html.Div("All", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"a"},
                   {"label":html.Div("Last", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"l", "disabled":False}]
        xaxis_text_style = {"textAlign":"center", "color":"black", "height":"1.5rem"}
        xaxis_line_style = {"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}
        xaxis_disabled = False; xaxis_value = no_update
        xaxis_a0_style = {"textAlign":"right", "color":"black", "height":"1.5rem", "width":"48px"}
        xaxis_an1a0_style = {"textAlign":"left", "color":"black", "height":"1.5rem", "width":"103px"}
        rel_text_style = {"textAlign":"center", "color":"black", "height":"1.5rem"}; rel_line_style = {"color":border_color, "margin-top":"1px", "margin-bottom":"1px"}
        rel_value = no_update
        rel_options = [{"label":html.Div("Absolute", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"abs"},
                    {"label":html.Div("Relative to", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"black"}), "value":"rel", "disabled":False}]
        rel_drop_options = [{"label":html.Div(f"{a:.0%}", style={"color":"black"}), "value":a} for a in betas if a <= 0.7]

    else:
        text_style = {"textAlign":"center", "color":"silver", "height":"1.5rem"}
        line_style = {"color":"silver", "margin-top":"1px", "margin-bottom":"1px"}
        mode = "a"; last_style = {"color":"silver"}
        options = [{"label":html.Div("All", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"silver"}), "value":"a"},
                   {"label":html.Div("Last", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"silver"}), "value":"l", "disabled":True}]
        xaxis_text_style = {"textAlign":"center", "color":"silver", "height":"1.5rem"}
        xaxis_line_style = {"color":"silver", "margin-top":"1px", "margin-bottom":"1px"}
        xaxis_disabled = True; xaxis_value = False
        xaxis_a0_style = {"textAlign":"right", "color":"silver", "height":"1.5rem", "width":"48px"}
        xaxis_an1a0_style = {"textAlign":"left", "color":"silver", "height":"1.5rem", "width":"103px"}
        rel_text_style = {"textAlign":"center", "color":"silver", "height":"1.5rem"}; rel_line_style = {"color":"silver", "margin-top":"1px", "margin-bottom":"1px"}
        rel_value = "abs"
        rel_options = [{"label":html.Div("Absolute", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"silver"}), "value":"abs"},
                        {"label":html.Div("Relative to", style={"display":"inline", "padding-left":"3px", "padding-right":"10px", "color":"silver"}), "value":"rel", "disabled":True}]
        rel_drop_options = [{"label":html.Div(f"{a:.0%}", style={"color":"silver"}), "value":a} for a in betas if a <= 0.7]

    return text_style, line_style, mode, options, last_style, xaxis_text_style, xaxis_line_style, xaxis_disabled, xaxis_value, xaxis_a0_style, xaxis_an1a0_style, rel_text_style, rel_line_style, rel_value, rel_options, rel_drop_options

@callback(
    Output(npoints_last, component_property="disabled"),
    Input(npoints_mode, component_property="value")
)
def npoints_input_disabling(mode):

    if mode == "a": return True
    else: return False

@callback(
    Output(relative_last, component_property="disabled"),
    Input(relative_mode, component_property="value")
)
def relative_input_disabling(mode):

    if mode == "abs": return True
    else: return False

@callback(
    Output(side_filter, component_property="is_open"),
    Input(filter, component_property="n_clicks"),
    State(side_filter, component_property="is_open")
)
def toggle_offcanvas_filters(n1, is_open):
    if n1:
        return not is_open
    return is_open