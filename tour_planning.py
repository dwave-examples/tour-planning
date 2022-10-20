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

locomotion = {
    "walk": {"Speed": 1, "Cost": 0, "Exercise": 1},
    "cycle": {"Speed": 3, "Cost": 2, "Exercise": 2},
     "bus": {"Speed": 4, "Cost": 3, "Exercise": 0},
     "drive": {"Speed": 7, "Cost": 5, "Exercise": 0}}
modes = locomotion.keys()  # global
num_modes = len(modes)

def set_legs(num_legs, min_leg_length, max_leg_length, tollbooths=True):
    """Create legs of random length within the configured ranges."""

    toll_probablity = 0.2
    if not tollbooths:
        toll_probablity = 0

    return [{"length": round((max_leg_length - min_leg_length)*random.random() \
        + min_leg_length, 1),
             "uphill": round(10*random.random(), 1),
             "toll": bool(np.random.choice([True, False], 1,
                p=[toll_probablity, 1 - toll_probablity])[0])}
        for i in range(num_legs)]

def average_tour_budget(legs):
    """Return average values of tour cost & time for the given legs.
    Initialization only.
    """

    legs_total = sum(l["length"] for l in legs)
    costs = [c["Cost"] for c in locomotion.values()]
    speeds = [s["Speed"] for s in locomotion.values()]
    max_cost = round(legs_total * np.mean([min(costs), max(costs)]))
    max_time = round(legs_total / np.mean([min(speeds), max(speeds)]))

    return max_cost, max_time

def tour_budget_boundaries(legs, locomotion_vals):
    """Return boundary values of tour cost & time for the given legs."""

    legs_total = sum(l["length"] for l in legs)
    costs = [locomotion_vals[mode][1] for mode in locomotion_vals.keys()]
    speeds = [locomotion_vals[mode][0] for mode in locomotion_vals.keys()]
    cost_min = round(legs_total * min(costs), 1)
    cost_max = round(legs_total * max(costs), 1)
    cost_avg = round(legs_total * np.mean([min(costs), max(costs)]), 1)
    time_avg = round(legs_total / np.mean([min(speeds), max(speeds)]), 1)
    time_min = round(legs_total / max(speeds), 1)
    time_max = round(legs_total / min(speeds), 1)

    return {"cost_min": cost_min, "cost_max": cost_max, "cost_avg": cost_avg,
        "time_min": time_min, "time_max": time_max, "time_avg": time_avg}

locomotion_ranges = {f"{mode}_{measure}": [0, 100] if measure != "speed" else
    [1, 100] for mode in locomotion.keys()
    for measure in [key.lower() for key in locomotion[mode].keys()]}

leg_ranges = {"num_legs": [5, 100],
    "max_leg_length": [1, 20],
    "min_leg_length": [1, 20]}

slope_ranges = {"max_leg_slope": [0, 10]}

weight_ranges = {"weight_cost": [0, 100000],
    "weight_time": [0, 100000],
    "weight_slope": [0, 100000],}

budget_ranges =  {"max_cost": [0, 100000],
    "max_time": [0, 100000]}

locomotion_init_values = {f"{mode}_{measure}": val for mode in locomotion.keys()
    for measure, val in {key.lower(): val for key, val in locomotion[mode].items()}.items()}

leg_init_values = {"num_legs": 10, "max_leg_length": 10, "min_leg_length": 2}

slope_init_values ={"max_leg_slope": 6}

weight_init_values = {"weight_cost": 100, "weight_time": 30, "weight_slope": 150}

budget_init_values = {}
budget_init_values["max_cost"], budget_init_values["max_time"] = \
    average_tour_budget(set_legs(**leg_init_values))

names_locomotion_inputs = list(locomotion_ranges.keys())
names_leg_inputs = list(leg_ranges.keys())
names_slope_inputs = list(slope_ranges.keys())
names_weight_inputs = list(weight_ranges.keys())
names_budget_inputs = list(budget_ranges.keys())
MAX_SOLVER_RUNTIME = 600

def _calculate_total(t, measure, legs, locomotion_vals):
    """Helper function for building the CQM."""

    num_legs = len(legs)

    if measure == "Exercise":
        return dimod.quicksum(
            t[i]*locomotion_vals[t[i].variables[0].split("_")[0]][2] *
            legs[i//num_modes]["length"]*legs[i//num_modes]["uphill"] for
            i in range(num_modes*num_legs))
    elif measure == "Time":

        return dimod.quicksum(
            t[i]*legs[i//num_modes]["length"]/locomotion_vals[t[i].variables[0].split("_")[0]][0] for
            i in range(num_modes*num_legs))
    else: # measure == "Cost"
        return dimod.quicksum(t[i]*locomotion_vals[t[i].variables[0].split("_")[0]][1] *
        legs[i//num_modes]["length"] for
        i in range(num_modes*num_legs))

def build_cqm(legs, modes, max_leg_slope, max_cost, max_time,
    weights, penalties, locomotion_vals):
    """Build CQM for maximizing exercise. """

    num_legs = len(legs)
    t= [dimod.Binary(f"{mode}_{i}") for i in range(num_legs) for mode in locomotion.keys()]

    cqm = dimod.ConstrainedQuadraticModel()
    cqm.set_objective(-_calculate_total(t, "Exercise", legs, locomotion_vals))

    for leg in range(num_legs):
        cqm.add_constraint(dimod.quicksum(t[num_modes*leg:num_modes*leg+num_modes]) == 1,
            label=f"One-hot leg{leg}")
    cqm.add_constraint(_calculate_total(t, "Cost", legs, locomotion_vals) <= max_cost, label="Total cost",
        weight=weights["cost"], penalty=penalties["cost"])
    cqm.add_constraint(_calculate_total(t, "Time", legs, locomotion_vals) <= max_time,
        label="Total time", weight=weights["time"], penalty=penalties["time"])

    drive_index = list(modes).index("drive")
    cycle_index = list(modes).index("cycle")
    walk_index = list(modes).index("walk")
    for leg in range(num_legs):
         if legs[leg]["toll"]:
             cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][drive_index] == 0,
                label=f"Toll to drive on leg {leg}")
         cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][cycle_index] * \
            legs[leg]["uphill"] <= max_leg_slope,
            label=f"Too steep to cycle on leg {leg}", weight=weights["slope"],
            penalty=penalties["slope"])
         cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][walk_index] * \
            legs[leg]["uphill"] <= max_leg_slope,
            label=f"Too steep to walk on leg {leg}", weight=weights["slope"],
            penalty=penalties["slope"])

    return cqm
