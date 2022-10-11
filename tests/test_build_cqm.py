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
import pytest
import random

import dimod

from tour_planning import names_leg_inputs, names_budget_inputs, names_weight_inputs
from tour_planning import leg_ranges, budget_ranges, weight_ranges, modes
from tour_planning import build_cqm

legs1 = [{"length": 10, "uphill": 5, "toll": False},
    {"length": 20, "uphill": 10, "toll": True}]
legs2 = [{"length": 30, "uphill": 5, "toll": False},
    {"length": 40, "uphill": 6, "toll": True},
    {"length": 50, "uphill": 7, "toll": False},
    {"length": 60, "uphill": 8, "toll": True}]

parametrize_names = "legs, modes, max_leg_slope, max_cost, max_time," + \
    " weights, penalties"

parametrize_vals = [(legs1, modes, 10, 10, 10, {"cost": None, "time": 55, "slope": None},
    {"cost": "linear", "time": "linear", "slope": "quadratic"}),
    (legs2, modes, 10, 10, 10, {"cost": None, "time": 55, "slope": None},
        {"cost": "linear", "time": "linear", "slope": "quadratic"})]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_build_cqm(legs, modes, max_leg_slope, max_cost,
    max_time, weights, penalties):
    """Minimal, simple testing that CQM builds correctly."""

    output = build_cqm(legs, modes, max_leg_slope, max_cost,
        max_time, weights, penalties)

    assert type(output) == dimod.ConstrainedQuadraticModel
    assert len(output.constraints) >= 2 + len(legs)
    assert len(output.variables) == len(modes)*len(legs)
    assert output.constraints["Total cost"].rhs == max_cost
    assert output.constraints["Total time"].rhs == max_time
    assert "walk_0 + cycle_0 + bus_0 + drive_0" in output.constraints["One-hot leg0"].to_polystring()
