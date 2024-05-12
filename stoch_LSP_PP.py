from pickle import load, dump
from plotly.express.colors import sample_colorscale
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

class data_mgmt():

    @staticmethod
    def import_data(experiment, page, st, container):

        file = open(f"./Experiments/Parameters/Global_{experiment}", "rb")
        (T, S, G, n, h, c, f, C) = load(file); file.close()

        setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem = dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict()
        for tup in container:
            
            if page == 1: prefix = "Age_service_level"; a,b = tup; beta = 0; epsilon = 1
            elif page == 2: prefix = "TP_service_level"; b,beta = tup; a = 0.4; epsilon = 1

            file = open(f"./Experiments/Performance metrics/{experiment}/{prefix}_{a,b}_{beta}_{epsilon}_stat-{st}", "rb")
            (setup[tup], holding[tup], production[tup], total[tup], period_sl[tup], total_sl[tup], waste_prod[tup], waste_dem[tup]) = load(file); file.close()

        return (T, S, G, n, h, c, f, C), (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem)

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
    def filter_data_fresh(a0, vals0, an1, valsn1):

        b0 = [a for a in a0 if a >= vals0[0] and a <= vals0[1]]
        bn1 = [b for b in an1 if b >= valsn1[0] and b <= valsn1[1]]

        return b0, bn1
    
    @staticmethod
    def filter_data_tp(an1, valsn1):

        b0 = [0.4]; bn1 = [b for b in an1 if b >= valsn1[0] and b <= valsn1[1]]

        return b0, bn1

class charts():

    @staticmethod
    def generate_plot_specifics(view_bool, mode, last, xaxis_bool, b0, bn1):

        if view_bool:
            cols = sample_colorscale("plasma",[(bn1[-1]-b)/(bn1[-1]-bn1[0]) for b in bn1])
            y_axis_container = bn1
            
            x_complete = {b:[a for a in b0 if a <= b][::-1] for b in bn1}
            x_axis_container = {b:x_complete[b][:np.min((len(x_complete[b]),last))] if mode == "l" else x_complete[b] for b in bn1}
            hover_text = "α(0)"; legend_title = r"$\alpha_{n-1}$"
            if not xaxis_bool:
                x_axis_vals = b0+[1]
                x_ax_title = r"$\alpha_0$"
            else:
                x_axis_container = {b:[round(b-a,3) for a in x_axis_container[b]] for b in bn1}
                x_axis_vals = list(set(x_axis_container[bn1[-1]]+x_axis_container[bn1[-2]]))
                x_ax_title = r"$\alpha_{n-1}-\alpha_0$" + f"(pp)"

            fresh_prod_sl = {"ticks":"outside", "ticktext":[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in b0]}
            total_prod_sl = {"ticks":"", "ticktext":[f"{b:.0%}" for b in bn1]}
        else:
            cols = sample_colorscale("turbo",[(a-b0[0])/(b0[-1]-b0[0]) for a in b0])
            y_axis_container = b0; x_axis_container = {a:[b for b in bn1 if a <= b] for a in b0}; x_axis_vals = bn1+[1]
            hover_text = "α(n-1)"; x_ax_title = r"$\alpha_{n-1}$"; legend_title = r"$\alpha_0$"

            fresh_prod_sl = {"ticks":"", "ticktext":[f"{a:.0%}" for a in b0]}
            total_prod_sl = {"ticks":"outside", "ticktext":[f"{b:.0%}" if b*100 % 10 == 0 else "" for b in bn1]}
        
        if xaxis_bool: x_axis_texts = [f"{100*x:.0f}" if x*100 % 5 == 0 else "" for x in x_axis_vals]
        else: x_axis_texts = [f"{x:.0%}" if x*100 % 10 == 0 else "" for x in x_axis_vals]
        
        return x_axis_vals, x_axis_container, y_axis_container, cols, hover_text, x_ax_title, legend_title, fresh_prod_sl, total_prod_sl, x_axis_texts

    @staticmethod
    def plot_service_level_analysis(b0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, st, specifics, xaxis_bool):

        x_axis_vals, x_axis_container, y_axis_container, cols, hover_text, x_ax_title, legend_title, fresh_prod_sl, total_prod_sl, x_axis_texts = specifics

        if st == "stat": s1 = "Average capacity utilization"; s2 = "Production cost"
        else: s1 = "Exp. average capacity utilization"; s2 = "Expected production cost"

        fig = make_subplots(rows=2, cols=5, horizontal_spacing=0.05, vertical_spacing=0.15, subplot_titles=["Total expected cost","Proportion of production days",s1,s2,"Expected holding cost",
                                                        "Achieved fresh produce fill rate","Achieved overall fill rate","Waste level (/prod.)","Waste level (/dem.)",None])

        ix=0
        for y in y_axis_container:
            if view_bool: comb = {x:(x,y) for x in x_axis_container[y]} if not xaxis_bool else {x:(round(y-x,3),y) for x in x_axis_container[y]}
            else: comb = {x:(y,x) for x in x_axis_container[y]}

            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([setup[comb[x]][rep]/(f*len(T)) for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=1, col=2)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[comb[x]][rep]*f/(C*setup[comb[x]][rep]*c) for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Utilization = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=3)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([production[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=4)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([holding[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=1, col=5)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total_sl[comb[x]][rep][0] for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Fresh produce fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}", legendgroup=f"{y:.1%}", showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([total_sl[comb[x]][rep][G[-1]] for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Overall fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=2, col=2)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_prod[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=False), row=2, col=3)
            fig.add_trace(go.Scatter(x=x_axis_container[y], y=[np.average([waste_dem[comb[x]][rep] for rep in reps]) for x in x_axis_container[y]], customdata=x_axis_container[y], mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{y:.1%}" , legendgroup=f"{y:.1%}", showlegend=True), row=2, col=4)
            ix += 1

        for i in range(1,6):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black", "size":10})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
        fig.update_yaxes(tickformat=".1%", row=1, col=2)
        fig.update_yaxes(tickformat=".1%", row=1, col=3)

        for i in range(1,5):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_vals, ticktext=x_axis_texts, showline=True, linewidth=1, linecolor="black", row=2, col=i, tickfont={"color":"black", "size":10})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=b0, ticks=fresh_prod_sl["ticks"], ticktext=fresh_prod_sl["ticktext"], row=2, col=1, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=bn1, ticks=total_prod_sl["ticks"], ticktext=total_prod_sl["ticktext"], row=2, col=2, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=3, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=4, tickfont={"color":"black"})

        fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":40}, legend={"x":0.875, "y":0, "xref":"paper", "yref":"paper", "itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=700)
        fig.update_layout(shapes=[dict(type="line", xref='paper', yref='paper', x0=-0.1, y0=0.475, x1=1.1, y1=0.475, line=dict(color="black", width=1))], hovermode="x" if hover_bool else "closest")
        fig.update_annotations(font_color="black")

        return fig

    @staticmethod
    def plot_tp_service_level_analysis(bn1, epsilons, diff_epsilons, tot_fr, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, st):

        if st == "stat": s1 = "Average lot size"; s2 = "Production cost"
        else: s1 = "Expected average lot size"; s2 = "Expected production cost"

        fig = make_subplots(rows=2, cols=5, horizontal_spacing=0.05, vertical_spacing=0.15, subplot_titles=["Total expected cost","Setup operations",s1,s2,"Expected holding cost",
                                                        "Achieved fresh produce fill rate","Achieved overall fill rate","Waste level (/prod.)","Waste level (/dem.)",None])

        if view_bool:
            cols = sample_colorscale("plasma",[(bn1[-1]-b)/(bn1[-1]-bn1[0]) for b in bn1])
            y_axis_container = bn1; x_axis_container = epsilons; x_axis_values = diff_epsilons
            hover_text = "β"; x_ax_title = r"$\beta$"; legend_title = r"$\alpha_{n-1}$"

            total_prod_sl = {"ticks":"", "ticktext":[f"{b:.0%}" for b in bn1]}
        else:
            cols = sample_colorscale("electric",[(diff_epsilons[-1]-a)/(diff_epsilons[-1]-diff_epsilons[0]) for a in diff_epsilons])
            y_axis_container = diff_epsilons; x_axis_container = bn1; x_axis_values = bn1
            hover_text = "α(n-1)"; x_ax_title = r"$\alpha_{n-1}$"; legend_title = r"$\beta$"

            total_prod_sl = {"ticks":"outside", "ticktext":[f"{b:.0%}" if b*100 % 10 == 0 else "" for b in bn1]}

        ix=0
        for b in y_axis_container:
            if view_bool: xpoints = x_axis_container[b]; comb = {a:(b,a) for a in xpoints}
            else: xpoints = [a for a in bn1 if (a,b) in tot_fr]; comb = {a:(a,b) for a in xpoints}

            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([total[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Tot. Exp. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([setup[comb[a]][rep]/f for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Setups = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=1, col=2)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production[comb[a]][rep]*f/(setup[comb[a]][rep]*c) for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Avg. Lot Size = %{y:,.1f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=3)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([production[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Prod. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=4)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([holding[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Exp. Hold. Cost = %{y:,.0f}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=1, col=5)
            fig.add_trace(go.Scatter(x=xpoints, y=[round(np.average([total_sl[comb[a]][rep][0] for rep in reps]),3) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Fresh produce fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}", legendgroup=f"{b:.1%}", showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=xpoints, y=[round(np.average([total_sl[comb[a]][rep][G[-1]] for rep in reps]),3) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Overall fill rate = %{y:,.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=2, col=2)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_prod[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/prod) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=False), row=2, col=3)
            fig.add_trace(go.Scatter(x=xpoints, y=[np.average([waste_dem[comb[a]][rep] for rep in reps]) for a in xpoints], customdata=xpoints, mode="lines+markers", hovertemplate=hover_text+": %{customdata:.1%} <br>Waste (/dem) = %{y:.2%}", marker={"color":cols[ix]}, name=f"{b:.1%}" , legendgroup=f"{b:.1%}", showlegend=True), row=2, col=4)
            ix += 1

        for i in range(1,6):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_values, ticktext=[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in x_axis_values], showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
            fig.update_yaxes(showline=True, linewidth=1, linecolor="black", row=1, col=i, tickfont={"color":"black"})
        for i in range(1,5):
            fig.update_xaxes(title={"text":x_ax_title, "font":{"color":"black"}}, ticks="outside", tickmode="array", tickvals=x_axis_values, ticktext=[f"{a:.0%}" if a*100 % 10 == 0 else "" for a in x_axis_values], showline=True, linewidth=1, linecolor="black", row=2, col=i, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.0%", row=2, col=1, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickvals=bn1, ticks=total_prod_sl["ticks"], ticktext=total_prod_sl["ticktext"], row=2, col=2, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=3, tickfont={"color":"black"})
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", tickformat=",.1%", row=2, col=4, tickfont={"color":"black"})

        fig.update_layout(plot_bgcolor='white', margin={"l":20, "r":20, "b":40, "t":40}, legend={"x":0.875, "y":0, "xref":"paper", "yref":"paper", "itemwidth":40, "traceorder":"reversed", "valign":"middle", "xanchor":"left", "title":{"text":legend_title, "side":"top center"}, "font":{"size":16, "color":"black"}}, height=700)
        fig.update_layout(shapes=[dict(type="line", xref='paper', yref='paper', x0=-0.1, y0=0.475, x1=1.1, y1=0.475, line=dict(color="black", width=1))], hovermode="x" if hover_bool else "closest")
        fig.update_annotations(font_color="black")

        return fig

    @staticmethod
    def gen_ind_sl_analysis(data, page, container, b0, bn1, reps, st, view_bool, hover_bool, specifics, xaxis_bool):

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, st, container)
        (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem) = data_mgmt.process_data(S, metrics, reps, container); del metrics

        fig = charts.plot_service_level_analysis(b0, bn1, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, st, specifics, xaxis_bool)

        return fig

    @staticmethod
    def gen_ind_tp_sl_analysis(data, page, container, bn1, epsilons, diff_epsilons, reps, st, view_bool, hover_bool):

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, st, container)
        (setup, holding, production, total, period_sl, total_sl, waste_prod, waste_dem) = data_mgmt.process_data(S, metrics, reps, container); del metrics

        fig = charts.plot_tp_service_level_analysis(bn1, epsilons, diff_epsilons, container, reps, T, S, G, f, c, C, setup, holding, production, total, total_sl, waste_prod, waste_dem, view_bool, hover_bool, st)

        return fig
    
    @staticmethod
    def gen_comb_sl_analysis(data, page, alpha, b0, bn1, reps, view_bool, hover_bool, plot, share_y):

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, "stat", alpha)
        (setup1, holding1, production1, total1, period_sl1, total_sl1, waste_prod1, waste_dem1) = data_mgmt.process_data(S, metrics, reps, alpha); del metrics

        (T, S, G, n, h, c, f, C), metrics = data_mgmt.import_data(data, page, "dyn", alpha)
        (setup2, holding2, production2, total2, period_sl2, total_sl2, waste_prod2, waste_dem2) = data_mgmt.process_data(S, metrics, reps, alpha); del metrics

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

    

