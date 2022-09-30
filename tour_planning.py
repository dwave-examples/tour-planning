# Copyright 2022 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import random
import numpy as np
import pandas as pd

import dimod
from dwave.cloud.hybrid import Client     # TODO: move the client function to this file

transport = {
    'walk': {'Speed': 1, 'Cost': 0, 'Exercise': 1},
    'cycle': {'Speed': 3, 'Cost': 2, 'Exercise': 2},
     'bus': {'Speed': 4, 'Cost': 3, 'Exercise': 0},
     'drive': {'Speed': 7, 'Cost': 5, 'Exercise': 0}}
modes = transport.keys()  # global
num_modes = len(modes)

def set_legs(num_legs, leg_length_range, max_leg_slope):
    return [{'length': round((leg_length_range[1] - leg_length_range[0])*random.random() \
        + leg_length_range[0], 1),
             'uphill': round(max_leg_slope*random.random(), 1),
             'toll': bool(np.random.choice([True, False], 1, p=[0.2, 0.8])[0])} for i in range(num_legs)]

def budgets(legs):
    legs_total = sum(l["length"] for l in legs)
    costs = [c["Cost"] for c in transport.values()]
    speeds = [s["Speed"] for s in transport.values()]
    max_cost = round(legs_total * np.mean([min(costs), max(costs)]))
    max_time = round(legs_total / np.mean([min(speeds), max(speeds)]))

    return max_cost, max_time

init_cqm = {'weight_cost_input': [0, 10000, 100],
    'weight_time_input': [0, 10000, 30],
    'weight_slope_input': [0, 10000, 150],}

init_tour = {'num_legs': [5, 100, 10],
    'max_leg_length': [1, 20, 10],
    'min_leg_length': [1, 20, 2],
    'max_leg_slope': [0, 10, 8],
    'max_cost': [0, 100000, 0],
    'max_time': [0, 100000, 0],}

init_legs = {'legs': set_legs(init_tour['num_legs'][2],
    [init_tour['min_leg_length'][2], init_tour['max_leg_length'][2]],
    init_tour['max_leg_slope'][2])}

init_tour['max_cost'][2], init_tour['max_time'][2] = budgets(init_legs['legs'])

def calculate_total(t, measure, legs):
    """Helper function for building CQM.

    Args:
        tour (tour class): Tour.
        model (model class): CQM.

    Returns:
        Constrained Quadratic Model.
    """
    num_legs = len(legs)
    if measure == 'Exercise':
        return dimod.quicksum(t[i]*transport[t[i].variables[0].split('_')[0]]['Exercise']*legs[i//num_modes]['length']*legs[i//num_modes]['uphill'] for i in range(num_modes*num_legs))
    elif measure == 'Time':
        return dimod.quicksum(t[i]*legs[i//num_modes]['length']/transport[t[i].variables[0].split('_')[0]]['Speed'] for i in range(num_modes*num_legs))
    else:
        return dimod.quicksum(t[i]*transport[t[i].variables[0].split('_')[0]][measure]*legs[i//num_modes]['length'] for i in range(num_modes*num_legs))

def build_cqm(legs, modes, max_cost, max_time, weight_cost_input, weight_time_input,
    max_leg_slope, weight_slope_input):
    """Build CQM for maximizing exercise.

    Args:
        tour (tour class): Tour.
        model (model class): CQM.

    Returns:
        Constrained Quadratic Model.
    """
    num_legs = len(legs)
    t= [dimod.Binary(f'{mode}_{i}') for i in range(num_legs) for mode in transport.keys()]

    cqm = dimod.ConstrainedQuadraticModel()
    cqm.set_objective(-calculate_total(t, "Exercise", legs))

    for leg in range(num_legs):
        cqm.add_constraint(dimod.quicksum(t[num_modes*leg:num_modes*leg+num_modes]) == 1, label=f"One-hot leg{leg}")
    cqm.add_constraint(calculate_total(t, "Cost", legs) <= max_cost, label="Total cost", weight=weight_cost_input, penalty='quadratic')
    cqm.add_constraint(calculate_total(t, "Time", legs) <= max_time, label="Total time", weight=weight_time_input, penalty='linear')

    drive_index = list(modes).index('drive')
    cycle_index = list(modes).index('cycle')
    for leg in range(num_legs):
         if legs[leg]['toll']:
             cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][drive_index] == 0, label=f"Toll to drive on leg {leg}")
         if legs[leg]['uphill'] > max_leg_slope/2:
             cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][cycle_index] == 0, label=f"Too steep to cycle on leg {leg}", weight=weight_slope_input)

    return cqm
