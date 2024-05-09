import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash_daq as daq

from dash import Dash, dcc, html, Output, Input, no_update
from plotly.express.colors import sample_colorscale
from plotly.subplots import make_subplots
from pickle import load, dump

a0 = [0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]
an1 = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]
alpha = [(a,b) for a in a0 for b in an1 if a <= b]

container_bg = "mediumturquoise"
header_bg = "#2DB5AF"; header_text_color="black"
border_color = "#269A94"; light_bg = "#ACEAE7"

def import_data(experiment, st, alpha):

    file = open(f"./Experiments/Parameters/Global_{experiment}", "rb")
    (T, S, G, n, h, c, f, C) = load(file); file.close()

    setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem = dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict()
    for (a,b) in alpha:
        file = open(f"./Experiments/Performance metrics/Age_service_level_{a,b}_0_1_stat-{st}", "rb")
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

def plot_service_level_analysis(b0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, st):

    if st == "stat": s1 = "Average capacity utilization"; s2 = "Production cost"
    else: s1 = "Exp. average capacity utilization"; s2 = "Expected production cost"

    fig = make_subplots(rows=2, cols=5, horizontal_spacing=0.05, vertical_spacing=0.15, subplot_titles=["Total expected cost","Proportion of production days",s1,s2,"Expected holding cost",
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
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([setup[comb[a]][rep]/(f*len(T)) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production[comb[a]][rep]*f/(C*setup[comb[a]][rep]*c) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Lot Size = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=3)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=4)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([holding[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=5)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl[comb[a]][rep][0] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Fresh produce fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl[comb[a]][rep][G[-1]] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Overall fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=2, col=2)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_prod[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=2, col=3)
        fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_dem[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=True), row=2, col=4)
        ix += 1

    for i in range(1,6):
        fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_container, ticktext=[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in x_axis_container], showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
    fig.update_yaxes(tickformat=".1%", row=1, col=2)
    fig.update_yaxes(tickformat=".1%", row=1, col=3)

    for i in range(1,5):
        fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_container, ticktext=[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in x_axis_container], showline=True, linewidth=1, linecolor="black", row=2, col=i, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=b0, ticks=fresh_prod_sl["ticks"], ticktext=fresh_prod_sl["ticktext"], row=2, col=1, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=bn1, ticks=total_prod_sl["ticks"], ticktext=total_prod_sl["ticktext"], row=2, col=2, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=3, tickfont={"color":"black"})
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=4, tickfont={"color":"black"})

    fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":40}, legend={"x":0.875, "y":0, "xref":"paper", "yref":"paper", "itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=700)
    fig.update_layout(shapes=[dict(type="line", xref='paper', yref='paper', x0=-0.1, y0=0.475, x1=1.1, y1=0.475, line=dict(color="black", width=1))], hovermode="x" if hover_bool else "closest")
    fig.update_annotations(font_color="black")

    return fig

def gen_ind_sl_analysis(alpha, data, b0, bn1, reps, st, view_bool, hover_bool):

    (T, S, G, n, h, c, f, C), metrics = import_data(data, st, alpha)
    (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem) = process_data(S, metrics, reps, alpha); del metrics

    fig = plot_service_level_analysis(b0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, st)

    return fig

def gen_comb_sl_analysis(alpha, data, b0, bn1, reps, view_bool, hover_bool, plot, share_y):

    (T, S, G, n, h, c, f, C), metrics = import_data(data, "stat", alpha)
    (setup1, holding1, production1, total1, period_sl1, total_sl1, waste_prod1, waste_dem1) = process_data(S, metrics, reps, alpha); del metrics

    (T, S, G, n, h, c, f, C), metrics = import_data(data, "dyn", alpha)
    (setup2, holding2, production2, total2, period_sl2, total_sl2, waste_prod2, waste_dem2) = process_data(S, metrics, reps, alpha); del metrics

    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1, subplot_titles=["Static-static", "Static-dynamic"], shared_yaxes = True if len(share_y) else False)

    if view_bool:
        cols = sample_colorscale("plasma",[(bn1[-1]-b)/(bn1[-1]-bn1[0]) for b in bn1])
        y_axis_container = bn1; x_axis_container = b0
        hover_text = "α(0)"; x_ax_title = r"$\alpha_0$"; legend_title = r"$\alpha_{n-1}$"

        fresh_prod_sl = {"ticks":"outside", "ticktext":[f"{a:.1%}" if a*100 % 10 == 0 and a < 1 else f"{a:.0%}" if a == 1 else "" for a in b0+[1]]}
        total_prod_sl = {"ticks":"", "ticktext":[f"{b:.1%}" if b < 1 else f"{b:.0%}" for b in bn1+[1]]}
    else:
        cols = sample_colorscale("turbo",[(a-b0[0])/(b0[-1]-b0[0]) for a in b0])
        y_axis_container = b0; x_axis_container = bn1
        hover_text = "α(n-1)"; x_ax_title = r"$\alpha_{n-1}$"; legend_title = r"$\alpha_0$"

        fresh_prod_sl = {"ticks":"", "ticktext":[f"{a:.1%}" if a < 1 else f"{a:.0%}" for a in b0+[1]]}
        total_prod_sl = {"ticks":"outside", "ticktext":[f"{b:.1%}" if b*100 % 10 == 0 and b < 1 else (f"{b:.0%}" if b == 1 else "") for b in bn1+[1]]}
    
    ix=0
    for b in y_axis_container:
        if view_bool: xpoints = [a for a in x_axis_container if a <= b]; comb = {a:(a,b) for a in xpoints}
        else: xpoints = [a for a in x_axis_container if a >= b]; comb = {a:(b,a) for a in xpoints}

        if plot == "tot_cost":
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total1[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total2[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "setup":
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([setup1[comb[a]][rep]/(f*len(T)) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([setup2[comb[a]][rep]/(f*len(T)) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "lot_size":    
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production1[comb[a]][rep]*f/(C*setup1[comb[a]][rep]*c) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Lot Size = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production2[comb[a]][rep]*f/(C*setup2[comb[a]][rep]*c) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Lot Size = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "prod_cost":    
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production1[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production2[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "hold_cost":    
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([holding1[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([holding2[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "fresh_fr":    
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl1[comb[a]][rep][0] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Fresh produce fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl2[comb[a]][rep][0] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Fresh produce fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "over_fr":
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl1[comb[a]][rep][G[-1]] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Overall fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total_sl2[comb[a]][rep][G[-1]] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Overall fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "w_prod":    
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_prod1[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_prod2[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        elif plot == "w_dem":    
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_dem1[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_dem2[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=True), row=1, col=2)
        ix += 1

    for i in range(1,3):
        fig.update_xaxes(range=[x_axis_container[0]-0.025,1.025], title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_container+[1], ticktext=[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in x_axis_container+[1]], showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})

        if plot == "setup": fig.update_yaxes(tickformat=".1%")
        elif plot == "lot_size": fig.update_yaxes(tickformat=".1%")
        elif plot == "fresh_fr": fig.update_yaxes(range=[b0[0]-0.025, 1.025], showline=True, linewidth=1, linecolor="black", tickvals=b0+[1], ticks=fresh_prod_sl["ticks"], ticktext=fresh_prod_sl["ticktext"], row=1, col=i, tickfont={"color":"black"})
        elif plot == "over_fr": fig.update_yaxes(range=[bn1[0]-0.025, 1.025], showline=True, linewidth=1, linecolor="black", tickvals=bn1+[1], ticks=total_prod_sl["ticks"], ticktext=total_prod_sl["ticktext"], row=1, col=i, tickfont={"color":"black"})
        elif plot in ["w_prod","w_dem"]: fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=1, col=i, tickfont={"color":"black"})

    if view_bool and plot == "over_fr":
        for b in bn1+[1]:
            fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=1, layer="below")
            fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=2, layer="below")
    elif plot == "over_fr":
        for col in [1,2]:
            for b in bn1+[1]:
                fig.add_shape(type="line", x0 = bn1[0]-0.025, x1=b, y0=b, y1=b, xref="x", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
                fig.add_shape(type="line", y0 = bn1[0]-0.025, y1=b, x0=b, x1=b, yref="y", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
    elif view_bool and plot == "fresh_fr":
        for col in [1,2]:
            for b in b0+[1]:
                fig.add_shape(type="line", x0 = b0[0]-0.025, x1=b, y0=b, y1=b, xref="x", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
                fig.add_shape(type="line", y0 = b0[0]-0.025, y1=b, x0=b, x1=b, yref="y", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
    elif plot == "fresh_fr":
        for b in b0+[1]:
            fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=1, layer="below")
            fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=2, layer="below")

    fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":60}, legend={"itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=400)
    fig.update_layout(hovermode="x" if hover_bool else "closest")
    fig.update_layout(yaxis_showticklabels=True, yaxis2_showticklabels=True)
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
        
        ], justify="center", align="center", style={"width":"100%", "backgroundColor":container_bg, "margin-top":"10px"})

], fluid=True, style={"backgroundColor":container_bg})

@app.callback(
    Output(sl_analysis, component_property="figure"),
    Output(comb_sl, component_property="figure"),
    Output(strategy, component_property="children"),
    Output(ind_tab_title, component_property="children"),
    Input(data_input, component_property="value"),
    Input(view_switch, component_property="value"),
    Input(hover_switch, component_property="value"),
    Input(alpha0_range, component_property="value"),
    Input(alphan1_range, component_property="value"),
    Input(strategy, component_property="n_clicks"),
    Input(chart_radio, component_property="value"),
    Input(scale_check, component_property="value")
)
def update_layout(data, view_bool, hover_bool, range_0, range_n1, m, plot_radio, scale_y):

    
    b0, bn1 = filter_data(a0, range_0, an1, range_n1); reps = list(range(5))

    if m % 2 == 0: st = "stat"; but = "Switch to stat-dyn"; tit = "Static-static strategy Service Level analysis"
    else: st = "dyn"; but= "Switch to stat-stat"; tit = "Static-dynamic strategy Service Level analysis"

    fig1 = gen_ind_sl_analysis(alpha, data, b0, bn1, reps, st, view_bool, hover_bool)
    fig2 = gen_comb_sl_analysis(alpha, data, b0, bn1, reps, view_bool, hover_bool, plot_radio, scale_y)

    return fig1, fig2, but, tit

if __name__ == "__main__":
    app.run_server(debug=True)
