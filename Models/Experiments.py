import gurobipy as gb
import numpy as np
import os
from pickle import dump, load

def stat_stat_standard_model(T, G, S, phi, n, h, c, f, C, I0, d, alpha, beta = 0, epsilon = 1, MIPFocus = 0,  FIFO = 0, output = False, verbose = False, time = False, threads=0):

    m = gb.Model("Standard Model")
    Tt = {t:[mm for mm in range(np.max((1,t)),np.min((T[-1],t+n-1)) + 1)] for t in T+[-tt for tt in range(n)]}

    ######################################
    # DECISION VARIABLES
    ######################################

    # Whether there is production in period t \in T or not
    y = {t:m.addVar(name=f"y_{t}", vtype=gb.GRB.BINARY) for t in T}
    # Produced quantity in period t \in T
    x = {t:m.addVar(name=f"x_{t}", vtype=gb.GRB.CONTINUOUS) for t in T}
    # Amount of product of age g \in G that is used to fulfill demand in period t \in T
    z = {s:{(t,g):m.addVar(name=f"z_{s,t,g}", vtype=gb.GRB.CONTINUOUS) for t in T for g in G} for s in S}
    # Lost sales of period t \in T
    l = {s:{t:m.addVar(name=f"l_{s,t}", vtype=gb.GRB.CONTINUOUS) for t in T} for s in S}
    # Available inventory of product of age g \in G at the end of period t \in T
    I = {s:{(t,g):m.addVar(name=f"I_{s,t,g}", vtype=gb.GRB.CONTINUOUS) for t in T for g in G} for s in S}
    for s in S: I[s].update({(0,g):I0[g] for g in I0})

    ######################################
    # CONSTRAINTS
    ######################################

    for t in T:

        # Production capacity
        m.addConstr(x[t] <= np.max([np.min((C,sum(d[s][mm] for mm in Tt[t]))) for s in S])*y[t])

        for s in S:
            # Inventory of fresh produce
            m.addConstr(I[s][t,0] == x[t] - z[s][t,0])

            for g in G[1:]:
                # Inventory dynamics throughout the day   
                m.addConstr(I[s][t,g] == I[s][t-1,g-1] - z[s][t,g])

            # Demand fulfillment and lost sales modeling
            m.addConstr(gb.quicksum(z[s][t,g] for g in G) + l[s][t] == d[s][t])
        
        # Expected demand service level by time period
        m.addConstr(gb.quicksum(phi[s]*gb.quicksum(z[s][t,g] for g in G)/d[s][t] for s in S) >= beta)
    
    for g in G:
        # Total age service level constraint
        m.addConstr(gb.quicksum(phi[s]*gb.quicksum(z[s][t,k] for t in T for k in range(g+1))/sum(d[s][t] for t in T) for s in S) >= alpha[g])
    
    # Total waste control constraint
    m.addConstr(gb.quicksum(phi[s]*gb.quicksum(I[s][t,n-1] for t in T) for s in S) <= epsilon*gb.quicksum(x[t] for t in T))

    # FIFO constraints
    if FIFO == 1:
        gamma = {s:{(t,g):m.addVar(name=f"gamma_{s,t,g}",vtype=gb.GRB.BINARY) for t in T for g in G} for s in S}

        for s in S:
            for t in T:
                for g in G:
                    m.addConstr(I[s][t,g] <= np.min((C,sum(d[s][mm] for mm in Tt[t-g])))*(1-gamma[s][t,g]))

                    if g < G[-1]:
                        m.addConstr(gamma[s][t,g] <= gamma[s][t,g+1])
                        m.addConstr(z[s][t,g] <= d[s][t]*gamma[s][t,g+1])

    ######################################
    # OBJECTIVE FUNCTION
    ######################################
    
    total_cost = gb.quicksum(f*y[t] + c*x[t] + h*gb.quicksum(phi[s]*gb.quicksum(I[s][t,g] for g in G) for s in S) for t in T)
    m.setObjective(total_cost)

    m.update()
    m.setParam("OutputFlag",output)
    m.setParam("MIPFocus",MIPFocus)
    m.setParam("Threads", threads)
    m.setParam("MIPGap",1e-5)
    m.optimize()

    ######################################
    # RESULTS RETRIEVING
    ######################################

    y = {t:round(y[t].x) for t in T}
    x = {t:round(x[t].x,10) for t in T}
    z = {s:{(t,g):round(z[s][t,g].x,10) for t in T for g in G} for s in S}
    l = {s:{t:round(l[s][t].x,10) for t in T} for s in S}
    w = {s:{t:round(I[s][t,n-1].x,10) for t in T} for s in S}
    I = {s:{(t,g):round(I[s][t,g].x,10) for t in T for g in G} for s in S}

    if verbose:
        print(f"\tObjective: {round(total_cost.getValue(),2)}")
        print(f"\t\tSetup: {f*sum(y[t] for t in T)}")
        print(f"\t\tExp. Holding: {h*sum(phi[s]*sum(I[s][t,g] for t in T for g in G) for s in S)}")
        print(f"\tRuntime: {round(m.runTime,4)}\n")

    return y, x, z, l, w, I


def get_costs_results(T, G, S, f, c, h, y, x, I, reps):

    setup, production, holding, total = dict(), dict(), dict(), dict()
    for ix in range(reps):
        setup[ix] = f*sum(y[ix][t] for t in T)
        production[ix] = c*sum(x[ix][t] for t in T)
        holding[ix] = [h*sum(I[ix][s][t,g] for t in T for g in G) for s in S]
        total[ix] = [setup[ix] + production[ix] + holding[ix][s-1] for s in S]

    return setup, holding, production, total

def get_service_level_results(T, G, S, d, z, reps):

    period_sl = {ix:{(t,g):[sum(z[ix][s][t,k] for k in range(g+1))/d[ix][s][t] for s in S] for t in T for g in G} for ix in range(reps)}
    total_sl = {ix:{g:[sum(z[ix][s][t,k] for t in T for k in range(g+1))/sum(d[ix][s][t] for t in T) for s in S] for g in G} for ix in range(reps)}

    return period_sl, total_sl

def get_waste_results(T, S, n, x, I, reps):

    waste = {ix:[sum(I[ix][s][t,n-1] for t in T)/sum(x[ix][t] for t in T) for s in S] for ix in range(reps)}

    return waste


def export_global_parameters(tup):

    new_dir = f"./Experiments/Parameters/"
    if not os.path.exists(new_dir): os.makedirs(new_dir)
    file = open(new_dir+f"Global_T{len(T)}_S{len(S)}_n{n}", "wb")
    dump(tup, file); file.close()


def export_instance_parameters(tup, extra=""):

    new_dir = f"./Experiments/Parameters/"
    file = open(new_dir + f"Demand_T{len(T)}_S{len(S)}_n{n}" + extra, "wb")
    dump(tup, file); file.close()

def export_results(tup, ab, extra=""):

    new_dir = f"./Experiments/Results/"
    if not os.path.exists(new_dir): os.makedirs(new_dir)
    file = open(new_dir + f"Age_service_level_ix{ab}" + extra, "wb")
    dump(tup, file); file.close()

def export_performance_metrics(tup, ab, extra=""):

    new_dir = f"./Experiments/Performance metrics/"
    if not os.path.exists(new_dir): os.makedirs(new_dir)
    file = open(new_dir + f"Age_service_level_ix{ab}" + extra, "wb")
    dump(tup, file); file.close()

'''
    Global parameters
'''

file = open("C:/Users/ari_r/OneDrive - Universidad de los andes/Montreal 2024-10/stoch_LSP_PP/Experiments/Parameters/Global_T20_S150_n4", "rb")
(T, S, G, n, h, c, f, C) = load(file); file.close()

file = open("C:/Users/ari_r/OneDrive - Universidad de los andes/Montreal 2024-10/stoch_LSP_PP/Experiments/Parameters/Demand_T20_S150_n4_FIFO", "rb")
d = load(file); file.close(); reps = len(d); S = range(1,len(d[0])+1)

a0 = [0.975]; an1 = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]

# Parameters setting

I0 = {g:0 for g in G[:-1]}; phi = {s:1/len(S) for s in S}
alpha = {(a,b):dict(zip(G,[a if g < G[-1] else b for g in G])) for a in a0 for b in an1 if a <= b}

for (a,b) in alpha:

    print(f"\n----------- alpha_0 = {a:.1%}, alpha_n1 = {b:.1%}")
    # Results dictionaries
    y, x, z, l, w, I = dict(), dict(), dict(), dict(), dict(), dict()

    for ix in range(reps):

        print(f"\tRUNNING FOR INSTANCE {ix}")

        '''
            Run experiments
        '''

        y[ix], x[ix], z[ix], l[ix], w[ix], I[ix] = stat_stat_standard_model(T, G, S, phi, n, h, c, f, C, I0, d[ix], alpha[a,b], beta=0, epsilon=1, MIPFocus = 2, FIFO=1, verbose=False)
        print(f"\tDone {ix}")

    # Export results
    export_results((y, x, z, l, w, I), (a,b), extra="FIFO")

    '''
        Performance metrics
    '''

    holding, production, setup, total = get_costs_results(T, G, S, f, c, h, y, x, I, reps)
    period_sl, total_sl = get_service_level_results(T, G, S, d, z, reps)
    waste = get_waste_results(T, S, n, x, I, reps)

    # Export results
    export_performance_metrics((holding, production, setup, total, period_sl, total_sl, waste), (a,b), extra="FIFO")
