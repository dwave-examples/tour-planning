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

legs = [{"length": 10, "uphill": 5, "toll": False}]

parametrize_names = "legs, modes, max_leg_slope, max_cost, max_time," + \
    " weights, penalties"

parametrize_vals = [(legs, modes, 10, 10, 10, {"cost": None, "time": 55, "slope": None},
    {"cost": "linear", "time": "linear", "slope": "quadratic"})]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_build_cqm(legs, modes, max_leg_slope, max_cost,
    max_time, weights, penalties):
    """Test CQM built correctly."""

    output = build_cqm(legs, modes, max_leg_slope, max_cost,
        max_time, weights, penalties)

    assert type(output) == dimod.ConstrainedQuadraticModel
