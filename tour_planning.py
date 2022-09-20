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

import dimod
import random
import numpy as np
import pandas as pd

def calculate_total(t, measure, tour):
    if measure == 'Exercise':
        return dimod.quicksum(t[i]*tour.transport[t[i].variables[0].split('_')[0]]['Exercise']*tour.legs[i//tour.num_modes]['length']*tour.legs[i//tour.num_modes]['uphill'] for i in range(tour.num_modes*tour.num_legs))
    elif measure == 'Time':
        return dimod.quicksum(t[i]*tour.legs[i//tour.num_modes]['length']/tour.transport[t[i].variables[0].split('_')[0]]['Speed'] for i in range(tour.num_modes*tour.num_legs))
    else:
        return dimod.quicksum(t[i]*tour.transport[t[i].variables[0].split('_')[0]][measure]*tour.legs[i//tour.num_modes]['length'] for i in range(tour.num_modes*tour.num_legs))

def build_cqm(tour):
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
    cqm.add_constraint(calculate_total(t, "Cost", tour) <= tour.max_cost, label="Total cost", weight=100, penalty='quadratic')
    cqm.add_constraint(calculate_total(t, "Time", tour) <= tour.max_time, label="Total time", weight=30, penalty='linear')

    drive_index = list(tour.modes).index('drive')
    cycle_index = list(tour.modes).index('cycle')
    for leg in range(tour.num_legs):
         if tour.legs[leg]['toll']:
             cqm.add_constraint(t[tour.num_modes*leg:tour.num_modes*leg+tour.num_modes][drive_index] == 0, label=f"Toll to drive on leg {leg}")
         if tour.legs[leg]['uphill'] > tour.max_elevation/2:
             cqm.add_constraint(t[tour.num_modes*leg:tour.num_modes*leg+tour.num_modes][cycle_index] == 0, label=f"Too steep to cycle on leg {leg}", weight=150)

    return cqm

def solve_cqm(cqm, sampler):
    """Solve the CQM on Leap CQM hybrid solver.

    Args:
        G (networkx Graph)
        k (int):
            Maximum number of communities.

    Returns:
        DiscreteQuadraticModel
    """
    sampleset = sampler.sample_cqm(cqm, time_limit=5)
    sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
