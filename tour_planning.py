import random
import numpy as np
import pandas as pd

import dimod
from dwave.cloud.hybrid import Client

class job_submission():
    """

    """
    def __init__(self, profile):
        self.client = None
        self.problem_data_id = ''
        self.computation = None
        self.submission_id = ''
        self.status = "WAITING"
        self.result = None
        self.state = "READY"
        self.submission_time = None

class tour():
    """

    """
    def __init__(self):
        self.num_legs = 10
        self.max_length = 10
        self.min_length = 2
        self.max_leg_slope = 8
        self.transport = {
            'walk': {'Speed': 1, 'Cost': 0, 'Exercise': 1},
            'cycle': {'Speed': 3, 'Cost': 2, 'Exercise': 2},
             'bus': {'Speed': 4, 'Cost': 3, 'Exercise': 0},
             'drive': {'Speed': 7, 'Cost': 5, 'Exercise': 0}}
        self.update_config()

    def update_config(self):
        self.legs = [{'length': round((self.max_length - self.min_length)*random.random() + self.min_length, 1),
                 'uphill': round(self.max_leg_slope*random.random(), 1),
                 'toll': np.random.choice([True, False], 1, p=[0.2, 0.8])[0]} for i in range(self.num_legs)]

        self.max_cost = sum(l["length"] for l in self.legs)*np.mean([c["Cost"] for c in self.transport.values()])
        self.max_time = 0.5*sum(l["length"] for l in self.legs)/min(s["Speed"] for s in self.transport.values())

        self.modes = self.transport.keys()
        self.num_modes = len(self.modes)

class model():
    """

    """
    def __init__(self):
        self.cqm = None
        self.weight_cost = 100
        self.weight_time = 30
        self.weight_slope = 150

def calculate_total(t, measure, tour):
    if measure == 'Exercise':
        return dimod.quicksum(t[i]*tour.transport[t[i].variables[0].split('_')[0]]['Exercise']*tour.legs[i//tour.num_modes]['length']*tour.legs[i//tour.num_modes]['uphill'] for i in range(tour.num_modes*tour.num_legs))
    elif measure == 'Time':
        return dimod.quicksum(t[i]*tour.legs[i//tour.num_modes]['length']/tour.transport[t[i].variables[0].split('_')[0]]['Speed'] for i in range(tour.num_modes*tour.num_legs))
    else:
        return dimod.quicksum(t[i]*tour.transport[t[i].variables[0].split('_')[0]][measure]*tour.legs[i//tour.num_modes]['length'] for i in range(tour.num_modes*tour.num_legs))

def build_cqm(tour, model):
    """Build DQM for maximizing modularity.

    Args:
        G (networkx Graph)
        k (int):
            Maximum number of communities.

    Returns:
        DiscreteQuadraticModel
    """
    t= [dimod.Binary(f'{mode}_{i}') for i in range(tour.num_legs) for mode in tour.transport.keys()]

    cqm = dimod.ConstrainedQuadraticModel()
    cqm.set_objective(-calculate_total(t, "Exercise", tour))

    for leg in range(tour.num_legs):
        cqm.add_constraint(dimod.quicksum(t[tour.num_modes*leg:tour.num_modes*leg+tour.num_modes]) == 1, label=f"One-hot leg{leg}")
    cqm.add_constraint(calculate_total(t, "Cost", tour) <= tour.max_cost, label="Total cost", weight=model.weight_cost, penalty='quadratic')
    cqm.add_constraint(calculate_total(t, "Time", tour) <= tour.max_time, label="Total time", weight=model.weight_time, penalty='linear')

    drive_index = list(tour.modes).index('drive')
    cycle_index = list(tour.modes).index('cycle')
    for leg in range(tour.num_legs):
         if tour.legs[leg]['toll']:
             cqm.add_constraint(t[tour.num_modes*leg:tour.num_modes*leg+tour.num_modes][drive_index] == 0, label=f"Toll to drive on leg {leg}")
         if tour.legs[leg]['uphill'] > tour.max_leg_slope/2:
             cqm.add_constraint(t[tour.num_modes*leg:tour.num_modes*leg+tour.num_modes][cycle_index] == 0, label=f"Too steep to cycle on leg {leg}", weight=model.weight_slope)

    return cqm
