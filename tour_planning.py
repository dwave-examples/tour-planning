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
from dwave.system import LeapHybridCQMSampler

L = 10

transport = {
    'walk': {'Speed': 1, 'Cost': 0, 'Exercise': 1},
    'cycle': {'Speed': 3, 'Cost': 2, 'Exercise': 2},
     'bus': {'Speed': 4, 'Cost': 3, 'Exercise': 0},
     'drive': {'Speed': 7, 'Cost': 5, 'Exercise': 0}}

modes = transport.keys()
num_modes = len(modes)

MAX_LENGTH = 10
MIN_LENGTH = 0.2*MAX_LENGTH
MAX_ELEVATION = 8
legs = [{'length': round((MAX_LENGTH - MIN_LENGTH)*random.random() + MIN_LENGTH, 1),
         'uphill': round(MAX_ELEVATION*random.random(), 1),
         'toll': np.random.choice([True, False], 1, p=[0.2, 0.8])[0]} for i in range(L)]

max_cost = sum(l["length"] for l in legs)*np.mean([c["Cost"] for c in transport.values()])
max_time = 0.5*sum(l["length"] for l in legs)/min(s["Speed"] for s in transport.values())

t= [dimod.Binary(f'{mode}_{i}') for i in range(L) for mode in transport.keys()]

def calculate_total(t, measure):
    if measure == 'Exercise':
        return dimod.quicksum(t[i]*transport[t[i].variables[0].split('_')[0]]['Exercise']*legs[i//num_modes]['length']*legs[i//num_modes]['uphill'] for i in range(num_modes*L))
    elif measure == 'Time':
        return dimod.quicksum(t[i]*legs[i//num_modes]['length']/transport[t[i].variables[0].split('_')[0]]['Speed'] for i in range(num_modes*L))
    else:
        return dimod.quicksum(t[i]*transport[t[i].variables[0].split('_')[0]][measure]*legs[i//num_modes]['length'] for i in range(num_modes*L))


cqm = dimod.ConstrainedQuadraticModel()
cqm.set_objective(-calculate_total(t, "Exercise"))

for leg in range(L):
    cqm.add_constraint(dimod.quicksum(t[num_modes*leg:num_modes*leg+num_modes]) == 1, label=f"One-hot leg{leg}")
cqm.add_constraint(calculate_total(t, "Cost") <= max_cost, label="Total cost", weight=100, penalty='quadratic')
cqm.add_constraint(calculate_total(t, "Time") <= max_time, label="Total time", weight=30, penalty='linear')

drive_index = list(modes).index('drive')
cycle_index = list(modes).index('cycle')
for leg in range(L):
     if legs[leg]['toll']:
         cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][drive_index] == 0, label=f"Toll to drive on leg {leg}")
     if legs[leg]['uphill'] > MAX_ELEVATION/2:
         cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][cycle_index] == 0, label=f"Too steep to cycle on leg {leg}", weight=150)
