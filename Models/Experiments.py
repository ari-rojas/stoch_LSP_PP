import gurobipy as gb
import numpy as np
import os
from pickle import dump, load

def stat_stat_standard_model(T, G, S, phi, n, h, c, f, C, I0, d, alpha, beta = 0, epsilon = 1, MIPFocus = 0,  FIFO = False, output = False, verbose = False):

    m = gb.Model("Standard Model")

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
        m.addConstr(x[t] <= C*y[t])

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
    if FIFO:
        gamma = {s:{(t,g):m.addVar(name=f"gamma_{s,t,g}",vtype=gb.GRB.BINARY) for t in T for g in G} for s in S}

        for s in S:
            for t in T:
                for g in G:
                    m.addConstr(I[s][t,g] <= C*(1-gamma[s][t,g]))

                    if g < G[-1]:
                        m.addConstr(gamma[s][t,g] <= gamma[s][t,g+1])
                        m.addConstr(z[s][t,g] <= C*gamma[s][t,g+1])
    
    ######################################
    # OBJECTIVE FUNCTION
    ######################################
    
    m.setObjective(gb.quicksum(f*y[t] + c*x[t] + h*gb.quicksum(phi[s]*gb.quicksum(I[s][t,g] for g in G) for s in S) for t in T))

    m.update()
    m.setParam("OutputFlag",output)
    m.setParam("MIPFocus",MIPFocus)
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
        print(f"\tObjective: {round(m.getObjective().getValue(),2)}")
        print(f"\t\tSetup: {f*sum(y[t] for t in T)}")
        print(f"\t\tExp. Holding: {h*sum(phi[s]*sum(I[s][t,g] for t in T for g in G) for s in S)}")
        print(f"\tRuntime: {round(m.runTime,4)}\n")

    return y, x, z, l, w, I

def get_costs_results(T, G, S, f, c, h, a0, an1, y, x, I):

    setup, production, holding, total = dict(), dict(), dict(), dict()
    for a in a0:
        for b in an1:

            if a <= b:
                setup[a,b] = f*sum(y[a,b][t] for t in T)
                production[a,b] = c*sum(x[a,b][t] for t in T)
                holding[a,b] = [h*sum(I[a,b][s][t,g] for t in T for g in G) for s in S]
                total[a,b] = [setup[a,b] + production[a,b] + holding[a,b][s-1] for s in S]

    return setup, holding, production, total

def get_service_level_results(T, G, S, a0, an1, d, z):

    period_sl = {(a,b):{(t,g):[sum(z[a,b][s][t,k] for k in range(g+1))/d[s][t] for s in S] for t in T for g in G} for a in a0 for b in an1 if a <= b}
    total_sl = {(a,b):{g:[sum(z[a,b][s][t,k] for t in T for k in range(g+1))/sum(d[s][t] for t in T) for s in S] for g in G} for a in a0 for b in an1 if a <= b}

    return period_sl, total_sl

def get_waste_results(T, S, a0, an1, n, x, I):

    waste = {(a,b):[sum(I[a,b][s][t,n-1] for t in T)/sum(x[a,b][t] for t in T) for s in S] for a in a0 for b in an1 if a <= b}

    return waste


def export_global_parameters(tup):

    new_dir = f"./Experiments/Parameters/"
    if not os.path.exists(new_dir): os.makedirs(new_dir)
    file = open(new_dir+f"Global_T{len(T)}_S{len(S)}_n{n}", "wb")
    dump(tup, file); file.close()


def export_instance_parameters(tup):

    new_dir = f"./Experiments/Parameters/"
    file = open(new_dir + f"Age_service_level_ix{ix}", "wb")
    dump(tup, file); file.close()

def export_results(tup):

    new_dir = f"./Experiments/Results/"
    if not os.path.exists(new_dir): os.makedirs(new_dir)
    file = open(new_dir + f"Age_service_level_ix{ix}", "wb")
    dump(tup, file); file.close()

def export_performance_metrics(tup):

    new_dir = f"./Experiments/Performance metrics/"
    if not os.path.exists(new_dir): os.makedirs(new_dir)
    file = open(new_dir + f"Age_service_level_ix{ix}", "wb")
    dump(tup, file); file.close()

'''
    Global parameters
'''

# TODO
T = 20; S = 150; n = 4
a0 = [0.4, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]; an1 = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.975]

# Parameters setting
h = 8; c = 5*h; f = 2*15*h
T = list(range(1,T+1)); G = list(range(n)); S = list(range(1,S+1))
I0 = {g:0 for g in G[:-1]}; phi = {s:1/len(S) for s in S}
alpha = {(a,b):dict(zip(G,[a if g < G[-1] else b for g in G])) for a in a0 for b in an1 if a <= b}

export_global_parameters((T, S, G, n, h, c, f, a0, an1, alpha))

for ix in range(10):

    print(f"RUNNING FOR INSTANCE {ix}")

    '''
        Instance-specific parameters
    '''

    d = {s:{t:10+20*np.random.random() for t in T} for s in S}
    C = np.max([np.floor(2*sum(list(d[s].values()))/len(T)) for s in S])

    export_instance_parameters((d,C))

    '''
        Run experiments
    '''

    # Results dictionaries
    y, x, z, l, w, I = dict(), dict(), dict(), dict(), dict(), dict()

    for (a,b) in alpha:
        y[a,b], x[a,b], z[a,b], l[a,b], w[a,b], I[a,b] = stat_stat_standard_model(T, G, S, phi, n, h, c, f, C, I0, d, alpha[a,b], beta=0, epsilon=1, MIPFocus = 2, FIFO=True, verbose=True)
        print(f"\tDone {(a,b)}\n")

    # Export results
    export_results((y, x, z, l, w, I))

    '''
        Performance metrics
    '''

    holding, production, setup, total = get_costs_results(T, G, S, f, c, h, a0, an1, y, x, I)
    period_sl, total_sl = get_service_level_results(T, G, S, a0, an1, d, z)
    waste = get_waste_results(T, S, a0, an1, n, x, I)

    # Export results
    export_performance_metrics((holding, production, setup, total, period_sl, total_sl, waste))
