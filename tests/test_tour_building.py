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

import copy
import numpy as np
from parameterized import parameterized
import pandas as pd
import pytest
import random

import dimod

from tour_planning import names_leg_inputs, names_budget_inputs, names_weight_inputs
from tour_planning import leg_ranges, budget_ranges, weight_ranges, modes
from tour_planning import average_tour_budget, build_cqm, set_legs, tour_budget_boundaries

legs1 = [{"length": 10, "uphill": 5, "toll": False},
    {"length": 20, "uphill": 10, "toll": True}]
legs2 = [{"length": 30, "uphill": 5, "toll": False},
    {"length": 40, "uphill": 6, "toll": True},
    {"length": 50, "uphill": 7, "toll": False},
    {"length": 60, "uphill": 8, "toll": True}]

@pytest.mark.parametrize("legs, maximums", [(legs1, (75, 8)), (legs2, (450, 45))])
def test_average_tour_budget(legs, maximums):
    """Test that maximum costs and time are calculated correctly."""

    output = average_tour_budget(legs)

    assert output == maximums

locomotion_vals = {"walk": [1, 0, 1],
"cycle": [3, 2, 2],
"bus": [4, 3, 0],
"drive": [7, 5, 0]}

parametrize_vals = [
(legs1, locomotion_vals, {'cost_min': 0, 'cost_max': 150, 'cost_avg': 75, 'time_min': 4, 'time_max': 30, 'time_avg': 8}),
(legs2, locomotion_vals, {'cost_min': 0, 'cost_max': 900, 'cost_avg': 450, 'time_min': 26, 'time_max': 180, 'time_avg': 45})]

@pytest.mark.parametrize("legs, locomotion_vals, boundaries", parametrize_vals)
def test_tour_budget_boundaries(legs, locomotion_vals, boundaries):
    """Test that tour boundaries are calculated correctly."""

    output = tour_budget_boundaries(legs, locomotion_vals)

    assert output == boundaries

parametrize_names = "legs, modes, max_leg_slope, max_cost, max_time," + \
    " weights, penalties, locomotion_vals"

parametrize_vals = [(legs1, modes, 10, 10, 10, {"cost": None, "time": 55, "slope": None},
    {"cost": "linear", "time": "linear", "slope": "quadratic"}, locomotion_vals),
    (legs2, modes, 10, 10, 10, {"cost": None, "time": 55, "slope": None},
        {"cost": "linear", "time": "linear", "slope": "quadratic"}, locomotion_vals)]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_build_cqm(legs, modes, max_leg_slope, max_cost,
    max_time, weights, penalties, locomotion_vals):
    """Minimal, simple testing that CQM builds correctly."""

    output = build_cqm(legs, modes, max_leg_slope, max_cost,
        max_time, weights, penalties, locomotion_vals)

    assert type(output) == dimod.ConstrainedQuadraticModel
    assert len(output.constraints) >= 2 + len(legs)
    assert len(output.variables) == len(modes)*len(legs)
    assert output.constraints["Total cost"].rhs == max_cost
    assert output.constraints["Total time"].rhs == max_time
    assert "walk_0 + cycle_0 + bus_0 + drive_0" in output.constraints["One-hot leg0"].to_polystring()


parametrize_names = "num_legs_val, max_leg_length_val, min_leg_length_val, "

parametrize_vals = []
for i in range(5):
    leg_vals = [random.randint(leg_ranges[key][0], leg_ranges[key][1]) for key
        in names_leg_inputs]
    leg_vals = [leg_vals[0], max(leg_vals[0], leg_vals[1]),
        min(leg_vals[0], leg_vals[1])]
    parametrize_vals.append(tuple(leg_vals))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_set_legs(num_legs_val, max_leg_length_val,
    min_leg_length_val):
    """Test that legs are correctly generated."""

    output = set_legs(num_legs_val, min_leg_length_val, max_leg_length_val)

    df = pd.DataFrame(output)

    assert df.shape == (num_legs_val, 3)
    assert set(df.columns) - set(["length", "uphill", "toll"]) == set()
    assert df["length"].sum() >= num_legs_val * min_leg_length_val
    assert df["length"].sum() <= num_legs_val * max_leg_length_val
    set(df["toll"].unique()) == {False, True}
