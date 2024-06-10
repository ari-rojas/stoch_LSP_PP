from pickle import load, dump
from plotly.express.colors import sample_colorscale
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import os

class data_mgmt():

    @staticmethod
    def import_data(experiment, page, st, sl_type, container):

        file = open(f"./Experiments/Parameters/Global_{experiment}", "rb")
        (T, S, G, n, h, c, f, C) = load(file); file.close()

        setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem, lit_period_sl, lit_total_sl = dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict()
        for tup in container:
            
            if page == 1: prefix = "Age_service_level"; a,b = tup; beta = 0; epsilon = 1
            elif page == 2: prefix = "TP_service_level"; beta,b = tup; a = 0.4 if sl_type == "base" else 0; epsilon = 1

            file = open(f"./Experiments/Performance metrics/{experiment}/{prefix}_{a,b}_{beta}_{epsilon}_stat-{st}_{sl_type}", "rb")
            (setup[tup], holding[tup], production[tup], total[tup], period_sl[tup], total_sl[tup], waste_prod[tup], waste_dem[tup], lit_period_sl[tup], lit_total_sl[tup]) = load(file); file.close()

        return (T, S, G, n, h, c, f, C), (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem, lit_period_sl, lit_total_sl)

    @staticmethod
    def process_data(S, metrics, reps, container):

        metrics = list(metrics)
        for m in metrics:
            for tup in container:
                for rep in reps:

                    if isinstance(m[tup][rep], list):
                        m[tup][rep] = sum(m[tup][rep])/len(S)
        
        return tuple(metrics)

    @staticmethod
    def filter_data(complete_0, vals_0, complete_1, vals_1):

        cont_0 = [a for a in complete_0 if a >= vals_0[0] and a <= vals_0[1]]
        cont_1 = [b for b in complete_1 if b >= vals_1[0] and b <= vals_1[1]]

        return cont_0, cont_1

class charts():

    @staticmethod
    def get_tabs_titles(m):

        if m % 2 == 0: st = "stat"; but = "Switch to stat-dyn"; tit = "Static-static strategy Service Level analysis"
        else: st = "dyn"; but= "Switch to stat-stat"; tit = "Static-dynamic strategy Service Level analysis"

        return st, but, tit

    @staticmethod
    def generate_plot_specifics(page, view_bool, mode, last, xaxis_bool, cont_0, bn1):

        if view_bool:
            cols = sample_colorscale("plasma", [(bn1[-1]-b)/(bn1[-1]-bn1[0]) for b in bn1])
            y_axis_container = bn1
            
            x_complete = {b:[a for a in cont_0 if a <= b][::-1] for b in bn1}
            x_axis_container = {b:x_complete[b][:np.min((len(x_complete[b]),last))] if mode == "l" else x_complete[b] for b in bn1}
            hover_text = "α(0)" if page == 1 else "β"; legend_title = r"$\alpha_{n-1}$"
            if not xaxis_bool:
                x_axis_vals = cont_0+[1]
                x_ax_title = r"$\alpha_0$" if page == 1 else r"$\beta$"
            else:
                x_axis_container = {b:[round(b-a,3) for a in x_axis_container[b]] for b in bn1}
                x_axis_vals = list(set(x_axis_container[bn1[-1]]+x_axis_container[bn1[-2]])); x_axis_vals.sort()
                x_ax_title = r"$\alpha_{n-1}-\alpha_0 \left(pp\right)$" if page == 1 else r"$\alpha_{n-1}-\beta$ \left(pp\right)"

            fresh_prod_sl = {"vals":cont_0+[1] if page == 1 else [i/10 for i in range(4,11)], "ticks":"outside", "ticktext":[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in cont_0+[1]] if page == 1 else [f"{i/10:.0%}" for i in range(4,11)]}
            total_prod_sl = {"ticks":"", "ticktext":[f"{b:.0%}" for b in bn1+[1]]}
        else:
            col_map = "turbo" if page == 1 else "electric"
            cols = sample_colorscale(col_map, [(a-cont_0[0])/(cont_0[-1]-cont_0[0]) for a in cont_0])
            y_axis_container = cont_0; x_axis_container = {a:[b for b in bn1 if a <= b] for a in cont_0}; x_axis_vals = bn1+[1]
            hover_text = "α(n-1)"; x_ax_title = r"$\alpha_{n-1}$"; legend_title = r"$\alpha_0$" if page == 1 else r"$\beta$"

            fresh_prod_sl = {"vals":cont_0+[1], "ticks":"", "ticktext":[f"{a:.0%}" for a in cont_0+[1]]}
            total_prod_sl = {"ticks":"outside", "ticktext":[f"{b:.0%}" if b*100 % 10 == 0 else "" for b in bn1+[1]]}
        
        if xaxis_bool: x_axis_texts = [f"{100*x:.0f}" if x*100 % 5 == 0 else "" for x in x_axis_vals]; x_hover_text = {y:[round(y-x,3) for x in x_axis_container[y]] for y in y_axis_container}
        else: x_axis_texts = [f"{x:.0%}" if x*100 % 10 == 0 else "" for x in x_axis_vals]; x_hover_text = x_axis_container

        return x_axis_vals, x_axis_container, x_hover_text, y_axis_container, cols, hover_text, x_ax_title, legend_title, fresh_prod_sl, total_prod_sl, x_axis_texts

    @staticmethod
    def plot_service_level_analysis(cont_0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, lit_total_sl, view_bool, hover_bool, st, specifics, xaxis_bool):

        x_axis_vals, x_axis_container, x_hover_text, y_axis_container, cols, hover_text, x_ax_title, legend_title, fresh_prod_sl, total_prod_sl, x_axis_texts = specifics

        if st == "stat": s1 = "Average capacity utilization"; s2 = "Production cost"
        else: s1 = "Exp. average capacity utilization"; s2 = "Expected production cost"

        fig = make_subplots(rows=2, cols=5, horizontal_spacing=0.05, vertical_spacing=0.15, subplot_titles=["Total expected cost",s2,"Expected holding cost","Achieved fresh produce fill rate","Achieved overall fill rate",
                                                                                                            "Proportion of production days",s1,"Waste level (/prod.)","Waste level (/dem.)",None])

        ix=0
        for y in y_axis_container:
            if view_bool: comb = {x:(x,y) for x in x_axis_container[y]} if not xaxis_bool else {x:(round(y-x,3),y) for x in x_axis_container[y]}
            else: comb = {x:(y,x) for x in x_axis_container[y]}

            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=2)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([holding[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=3)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total_sl[comb[x]][rep][0] for rep in reps]) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y], [np.average([lit_total_sl[comb[x]][rep][0] for rep in reps]) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Fresh produce fill rate (scn) = %{y:,.2%} <br>Fresh produce fill rate (lit) = %{customdata[1]:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=4)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total_sl[comb[x]][rep][G[-1]] for rep in reps]) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y], [np.average([lit_total_sl[comb[x]][rep][G[-1]] for rep in reps]) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Overall fill rate (scn) = %{y:,.2%} <br>Overall fill rate (lit) = %{customdata[1]:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=1, col=5)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([setup[comb[x]][rep]/(f*len(T)) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[comb[x]][rep]*f/(C*setup[comb[x]][rep]*c) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Utilization = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=2, col=2)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_prod[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=2, col=3)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_dem[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True), row=2, col=4)
            ix += 1

        for i in range(1,6):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black", "size":10})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=fresh_prod_sl["vals"], ticks=fresh_prod_sl["ticks"], ticktext=fresh_prod_sl["ticktext"], row=1, col=4, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=bn1, ticks=total_prod_sl["ticks"], ticktext=total_prod_sl["ticktext"], row=1, col=5, tickfont={"color":"black"})

        for i in range(1,5):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=2, col=i, tickfont={"color":"black", "size":10})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=".1%", row=2, col=i, tickfont={"color":"black"})

        fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":40}, legend={"x":0.875, "y":0, "xref":"paper", "yref":"paper", "itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=700)
        fig.update_layout(shapes=[dict(type="line", xref='paper', yref='paper', x0=-0.1, y0=0.475, x1=1.1, y1=0.475, line=dict(color="black", width=1))], hovermode="x" if hover_bool else "closest")
        fig.update_annotations(font_color="black")

        return fig
    
    @staticmethod
    def plot_service_level_analysis_relative(cont_0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, lit_total_sl, view_bool, hover_bool, st, specifics, xaxis_bool, relative):

        x_axis_vals, x_axis_container, x_hover_text, y_axis_container, cols, hover_text, x_ax_title, legend_title, fresh_prod_sl, total_prod_sl, x_axis_texts = specifics

        if st == "stat": s1 = "Average capacity utilization"; s2 = "Production cost"
        else: s1 = "Exp. average capacity utilization"; s2 = "Expected production cost"

        fig = make_subplots(rows=2, cols=5, horizontal_spacing=0.05, vertical_spacing=0.15, subplot_titles=["Total expected cost",s2,"Expected holding cost","Achieved fresh produce fill rate","Achieved overall fill rate",
                                                                                                            "Proportion of production days",s1,"Waste level (/prod.)","Waste level (/dem.)",None])

        ix=0
        for y in y_axis_container:
            comb = {x:(x,y) for x in x_axis_container[y]} if not xaxis_bool else {x:(round(y-x,3),y) for x in x_axis_container[y]}
            rel = {x:(relative,y) for x in x_axis_container[y]}

            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total[comb[x]][rep] for rep in reps])/np.average([total[rel[x]][rep] for rep in reps])-1 for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:+,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[comb[x]][rep] for rep in reps])/np.average([production[rel[x]][rep] for rep in reps])-1 for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:+,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=2)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([holding[comb[x]][rep] for rep in reps])/np.average([holding[rel[x]][rep] for rep in reps])-1 for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:+,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=3)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[100*(np.average([total_sl[comb[x]][rep][0] for rep in reps])-comb[x][0]) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y],[100*(np.average([lit_total_sl[comb[x]][rep][0] for rep in reps])-comb[x][0]) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Fresh produce fill rate (scn) = %{y:+.2} pp <br>Fresh produce fill rate (lit) = %{customdata[1]:+.2} pp", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=4)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[100*(np.average([total_sl[comb[x]][rep][G[-1]] for rep in reps])-y) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y],[100*(np.average([lit_total_sl[comb[x]][rep][G[-1]] for rep in reps])-comb[x][0]) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Overall fill rate (scn) = %{y:+.2} pp <br>Overall fill rate (lit) = %{customdata[1]:+.2} pp", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=1, col=5)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([setup[comb[x]][rep]/(f*len(T)) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[comb[x]][rep]*f/(C*setup[comb[x]][rep]*c) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Utilization = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=2, col=2)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_prod[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=2, col=3)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_dem[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True), row=2, col=4)
            ix += 1

        for i in range(1,6):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black", "size":10})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
        for i in range(1,4):
            fig.update_yaxes(tickformat="+,.0%")
        fig.update_yaxes(title={"text":r"$\left(pp\right)$", "font":{"color":"black"}}, tickformat="+.1", row=1, col=4)
        fig.update_yaxes(title={"text":r"$\left(pp\right)$", "font":{"color":"black"}}, tickformat="+.1", row=1, col=5)

        for i in range(1,5):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=2, col=i, tickfont={"color":"black", "size":10})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=".1%", row=2, col=i, tickfont={"color":"black"})

        fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":40}, legend={"x":0.875, "y":0, "xref":"paper", "yref":"paper", "itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=700)
        fig.update_layout(shapes=[dict(type="line", xref='paper', yref='paper', x0=-0.1, y0=0.475, x1=1.1, y1=0.475, line=dict(color="black", width=1))], hovermode="x" if hover_bool else "closest")
        fig.update_annotations(font_color="black")

        return fig

    @staticmethod
    def gen_ind_sl_analysis(data, page, container, cont_0, bn1, reps, st, sl_type, view_bool, hover_bool, specifics, xaxis_bool):

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, st, sl_type, container)
        (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem, lit_period_sl, lit_total_sl) = data_mgmt.process_data(S, metrics, reps, container); del metrics

        fig = charts.plot_service_level_analysis(cont_0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, lit_total_sl, view_bool, hover_bool, st, specifics, xaxis_bool)

        return fig
    
    @staticmethod
    def gen_ind_sl_analysis_relative(data, page, container, cont_0, bn1, reps, st, sl_type, view_bool, hover_bool, specifics, xaxis_bool, relative):

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, st, sl_type, container)
        (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem, lit_period_sl, lit_total_sl) = data_mgmt.process_data(S, metrics, reps, container); del metrics

        fig = charts.plot_service_level_analysis_relative(cont_0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, lit_total_sl, view_bool, hover_bool, st, specifics, xaxis_bool, relative)

        return fig
    
    @staticmethod
    def gen_comb_sl_analysis(data, page, alpha, cont_0, bn1, reps, sl_type, view_bool, hover_bool, plot, share_y, specifics, xaxis_bool, download = False):

        setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem, lit_period_sl, lit_total_sl = dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict()

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, "stat", sl_type, alpha)
        (setup[1], holding[1], production[1], total[1], period_sl[1], total_sl[1], waste_prod[1], waste_dem[1], lit_period_sl[1], lit_total_sl[1]) = data_mgmt.process_data(S, metrics, reps, alpha); del metrics

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, "dyn", sl_type, alpha)
        (setup[2], holding[2], production[2], total[2], period_sl[2], total_sl[2], waste_prod[2], waste_dem[2], lit_period_sl[2], lit_total_sl[2]) = data_mgmt.process_data(S, metrics, reps, alpha); del metrics

        fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1, subplot_titles=["Static-static", "Static-dynamic"], shared_yaxes = True if len(share_y) else False)
        x_axis_vals, x_axis_container, x_hover_text, y_axis_container, cols, hover_text, x_ax_title, legend_title, fresh_prod_sl, total_prod_sl, x_axis_texts = specifics

        ix=0
        for y in y_axis_container:
            if view_bool: comb = {x:(x,y) for x in x_axis_container[y]} if not xaxis_bool else {x:(round(y-x,3),y) for x in x_axis_container[y]}
            else: comb = {x:(y,x) for x in x_axis_container[y]}

            for col in [1,2]:
                if plot == "tot_cost": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total[col][comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+ ": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "setup": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([setup[col][comb[x]][rep]/(f*len(T)) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "lot_size": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[col][comb[x]][rep]*f/(C*setup[col][comb[x]][rep]*c) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Utilization = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "prod_cost": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[col][comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "hold_cost": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([holding[col][comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "fresh_fr": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total_sl[col][comb[x]][rep][0] for rep in reps]) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y],[np.average([lit_total_sl[col][comb[x]][rep][0] for rep in reps]) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Fresh produce fill rate (scn) = %{y:,.2%} <br>Fresh produce fill rate (lit) = %{customdata[1]:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "over_fr": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total_sl[col][comb[x]][rep][G[-1]] for rep in reps]) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y],[np.average([lit_total_sl[col][comb[x]][rep][G[-1]] for rep in reps]) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Overall fill rate (scn) = %{y:,.2%} <br>Overall fill rate (lit) = %{customdata[1]:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "w_prod": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_prod[col][comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "w_dem": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_dem[col][comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
            ix += 1

        for i in range(1,3):
            fig.update_xaxes(range=[x_axis_vals[0]-0.02,x_axis_vals[-1]+0.02], title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})

            if plot == "setup": fig.update_yaxes(tickformat=".1%")
            elif plot == "lot_size": fig.update_yaxes(tickformat=".1%")
            elif plot == "fresh_fr": fig.update_yaxes(range=[fresh_prod_sl["vals"][0]-0.025, 1.025], showline=True, linewidth=1, linecolor="black", tickvals=fresh_prod_sl["vals"], ticks=fresh_prod_sl["ticks"], ticktext=fresh_prod_sl["ticktext"], row=1, col=i, tickfont={"color":"black"})
            elif plot == "over_fr": fig.update_yaxes(range=[bn1[0]-0.025, 1.025], showline=True, linewidth=1, linecolor="black", tickvals=bn1+[1], ticks=total_prod_sl["ticks"], ticktext=total_prod_sl["ticktext"], row=1, col=i, tickfont={"color":"black"})
            elif plot in ["w_prod","w_dem"]: fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=1, col=i, tickfont={"color":"black"})

        if view_bool and plot == "over_fr":
            for b in bn1+[1]:
                fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=1, layer="below")
                fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=2, layer="below")
        elif plot == "over_fr":
            for col in [1,2]:
                for b in bn1+[1]:
                    fig.add_shape(type="line", x0 = bn1[0]-0.02, x1=b, y0=b, y1=b, xref="x", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
                    fig.add_shape(type="line", y0 = bn1[0]-0.02, y1=b, x0=b, x1=b, yref="y", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
        elif view_bool and plot == "fresh_fr":
            for col in [1,2]:
                for b in fresh_prod_sl["vals"]:
                    fig.add_shape(type="line", x0 = fresh_prod_sl["vals"][0]-0.02, x1=b, y0=b, y1=b, xref="x", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
                    fig.add_shape(type="line", y0 = fresh_prod_sl["vals"][0]-0.02, y1=b, x0=b, x1=b, yref="y", line={"color":"black", "width":1, "dash":"dot"}, row=1, col=col, layer="below")
        elif plot == "fresh_fr":
            for b in fresh_prod_sl["vals"]:
                fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=1, layer="below")
                fig.add_hline(y=b, line_dash="dot", line_width=1, line_color="black", row=1, col=2, layer="below")

        fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":60}, legend={"itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=400)
        fig.update_layout(hovermode="x" if hover_bool else "closest")
        fig.update_layout(yaxis_showticklabels=True, yaxis2_showticklabels=True)
        fig.update_annotations(font_color="black")

        if download:

            if page == 1: prefix = "Fresh_SL"
            elif page == 2: prefix = "TP_SL"

            new_file = False; ix = 0
            while not new_file:
                if os.path.exists(f"./Images/{prefix}_{plot}_{ix}.png"): ix += 1
                else: new_file = True

            pio.write_image(fig, f"./Images/{prefix}_{plot}_{ix}.png", width=800, height=350, scale=6)
        
        return fig
    
    @staticmethod
    def gen_comb_sl_analysis_relative(data, page, alpha, cont_0, bn1, reps, sl_type, view_bool, hover_bool, plot, share_y, specifics, xaxis_bool, relative, download = False):

        setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem, lit_period_sl, lit_total_sl = dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict()

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, "stat", sl_type, alpha)
        (setup[1], holding[1], production[1], total[1], period_sl[1], total_sl[1], waste_prod[1], waste_dem[1], lit_period_sl[1], lit_total_sl[1]) = data_mgmt.process_data(S, metrics, reps, alpha); del metrics

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, "dyn", sl_type, alpha)
        (setup[2], holding[2], production[2], total[2], period_sl[2], total_sl[2], waste_prod[2], waste_dem[2], lit_period_sl[2], lit_total_sl[2]) = data_mgmt.process_data(S, metrics, reps, alpha); del metrics

        fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1, subplot_titles=["Static-static", "Static-dynamic"], shared_yaxes = True if len(share_y) else False)
        x_axis_vals, x_axis_container, x_hover_text, y_axis_container, cols, hover_text, x_ax_title, legend_title, fresh_prod_sl, total_prod_sl, x_axis_texts = specifics

        ix=0
        for y in y_axis_container:
            comb = {x:(x,y) for x in x_axis_container[y]} if not xaxis_bool else {x:(round(y-x,3),y) for x in x_axis_container[y]}
            rel = {x:(relative,y) for x in x_axis_container[y]}

            for col in [1,2]:
                if plot == "tot_cost": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total[col][comb[x]][rep] for rep in reps])/np.average([total[col][rel[x]][rep] for rep in reps])-1 for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+ ": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:+,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "setup": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([setup[col][comb[x]][rep]/(f*len(T)) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "lot_size": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[col][comb[x]][rep]*f/(C*setup[col][comb[x]][rep]*c) for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Utilization = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "prod_cost": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[col][comb[x]][rep] for rep in reps])/np.average([production[col][rel[x]][rep] for rep in reps])-1 for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:+,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "hold_cost": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([holding[col][comb[x]][rep] for rep in reps])/np.average([holding[col][rel[x]][rep] for rep in reps])-1 for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:+,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "fresh_fr": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[100*(np.average([total_sl[col][comb[x]][rep][0] for rep in reps])-comb[x][0]) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y], [100*(np.average([lit_total_sl[col][comb[x]][rep][0] for rep in reps])-comb[x][0]) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Fresh produce fill rate (scn) = %{y:+.2} pp <br>Fresh produce fill rate (lit) = %{customdata[1]:+.2} pp", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "over_fr": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[100*(np.average([total_sl[col][comb[x]][rep][G[-1]] for rep in reps])-y) for x in x_axis_container[y]], customdata=np.stack([x_hover_text[y], [100*(np.average([lit_total_sl[col][comb[x]][rep][G[-1]] for rep in reps])-y) for x in x_axis_container[y]]], axis=1), mode="lines+markers", hovertemplate=hover_text+": %{customdata[0]:.2%} <br>Overall fill rate (scn) = %{y:+.2} pp <br>Overall fill rate (lit) = %{customdata[1]:+.2} pp", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "w_prod": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_prod[col][comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
                elif plot == "w_dem": fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_dem[col][comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_hover_text[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True if col == 2 else False), row=1, col=col)
            ix += 1

        for i in range(1,3):
            fig.update_xaxes(range=[x_axis_vals[0]-0.02,x_axis_vals[-1]+0.02], title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})

            if plot in ["setup","lot_size"]: fig.update_yaxes(tickformat=".1%", row=1, col=i)
            elif plot in ["tot_cost","prod_cost","hold_cost"]: fig.update_yaxes(tickformat="+,.1%", row=1, col=i)
            elif plot in ["fresh_fr","over_fr"]: fig.update_yaxes(title={"text":r"$\left(pp\right)$", "font":{"color":"black"}}, tickformat=",.0f", row=1, col=i)
            elif plot in ["w_prod","w_dem"]: fig.update_yaxes(tickformat=",.1%", row=1, col=i)

        
        fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":60}, legend={"itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=400)
        fig.update_layout(hovermode="x" if hover_bool else "closest")
        fig.update_layout(yaxis_showticklabels=True, yaxis2_showticklabels=True)
        fig.update_annotations(font_color="black")

        if download:

            if page == 1: prefix = "Fresh_SL"
            elif page == 2: prefix = "TP_SL"

            new_file = False; ix = 0
            while not new_file:
                if os.path.exists(f"./Images/{prefix}_{plot}_{ix}.png"): ix += 1
                else: new_file = True

            pio.write_image(fig, f"./Images/{prefix}_{plot}_{ix}.png", width=800, height=350, scale=6)
        
        return fig

    

