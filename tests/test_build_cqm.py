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

from parameterized import parameterized
import pytest
from unittest.mock import patch

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

import dimod

from formatting import tour_from_json

from app import names_budget_inputs, names_weight_inputs
from app import generate_cqm

problem_print_placeholder = """
Configurable inputs have these supported ranges and current values:
"""

cqm_placeholder = " "

def mock_print(self):
    return self

parametrize_names = "changed_input_val, problem_print_code_val, max_leg_slope_val, " + \
    ", ".join([f'{key}_val ' for key in names_budget_inputs + names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_hardsoft_val ' for key in names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_penalty_val ' for key in names_weight_inputs]) + \
    ", cqm_print_val"

parametrize_constants = [8, 200, 20, 33, 44, 55, "soft", "soft", "hard", "linear",
    "linear", "quadratic"]
parametrize_vals = [("num_legs", problem_print_placeholder, *parametrize_constants, cqm_placeholder),
("max_time", problem_print_placeholder, *parametrize_constants, cqm_placeholder)]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("dimod.ConstrainedQuadraticModel.__str__", mock_print)
def test_build_cqm(changed_input_val, problem_print_code_val, max_leg_slope_val,
    max_cost_val, max_time_val, weight_cost_val, weight_time_val, weight_slope_val,
    weight_cost_hardsoft_val, weight_time_hardsoft_val, weight_slope_hardsoft_val,
    weight_cost_penalty_val, weight_time_penalty_val, weight_slope_penalty_val,
    cqm_print_val):
    """Test that a CQM is generated based on input signals."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{changed_input_val}.value"},
                {"prop_id": "problem_print_code.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_hardsoft.get(), weight_time_hardsoft.get(), \
            weight_slope_hardsoft.get(), weight_cost_penalty.get(), \
            weight_time_penalty.get(), weight_slope_penalty.get())

    changed_input.set(vars()["changed_input_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs + names_weight_inputs:
        globals()[key].set(vars()[key + "_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output) == dimod.ConstrainedQuadraticModel
    assert type(output.constraints["One-hot leg0"]) == dimod.sym.Eq
    assert type(output.constraints["Total time"]) == dimod.sym.Le

    #  Temporary use of internal method until a non-internal methos is availibele
    if weight_cost_hardsoft_val == "soft":
        output._soft["Total cost"] == dimod.constrained.SoftConstraint(weight=weight_cost_val,
            penalty='quadratic')
        output._soft["Total time"] == dimod.constrained.SoftConstraint(weight=weight_time_val,
            penalty='quadratic')
