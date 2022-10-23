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
from itertools import product

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

import dimod

from formatting import state_to_json, tour_from_json

from app import names_budget_inputs, names_weight_inputs
from app import generate_cqm

problem_print_placeholder = '[{"length": 9.4, "uphill": 0.1, "toll": false}, {"length": 6.9, "uphill": 2.5, "toll": false}]'

changed_input = ContextVar("changed_input")
problem_print_code = ContextVar("problem_print_code")
max_leg_slope = ContextVar("max_leg_slope")
for key in names_budget_inputs + names_weight_inputs:
    vars()[key] = ContextVar(f"{key}")
for key in names_weight_inputs:
    vars()[f"{key}_hardsoft"] = ContextVar(f"{key}_hardsoft")
for key in names_weight_inputs:
    vars()[f"{key}_penalty"] = ContextVar(f"{key}_penalty")
locomotion_state = ContextVar("locomotion_state")

state_vals = [{"prop_id": "max_leg_slope"}]
state_vals.extend([{"prop_id": f"{key}.value"} for key in
    names_budget_inputs + names_weight_inputs])
state_vals.extend([{"prop_id": f"{key}_hardsoft.value"} for key in names_weight_inputs])
state_vals.extend([{"prop_id": f"{key}_penalty.value"} for key in names_weight_inputs])
state_vals.extend([{"prop_id": "locomotion_state.children"}])

cqm_placeholder = " "

def mock_print(self):
    return self

locomotion_json = state_to_json({
    "walk": {"speed": 1, "cost": 0, "exercise": 1, "use": True},
    "cycle": {"speed": 3, "cost": 2, "exercise": 2, "use": True},
     "bus": {"speed": 4, "cost": 3, "exercise": 0, "use": True},
     "drive": {"speed": 7, "cost": 5, "exercise": 0, "use": True}})

parametrize_names = "trigger, changed_input_val, problem_print_code_val, max_leg_slope_val, " + \
    ", ".join([f'{key}_val ' for key in names_budget_inputs + names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_hardsoft_val ' for key in names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_penalty_val ' for key in names_weight_inputs]) + \
    ", locomotion_val, cqm_print_val"

parametrize_constants = ["num_legs", problem_print_placeholder, 8, 200, 20, 33, 44, 55, "soft", "soft", "hard", "linear",
    "linear", "quadratic", locomotion_json]
parametrize_vals = [("changed_input", *parametrize_constants, cqm_placeholder),
    ("problem_print_code", *parametrize_constants, cqm_placeholder),
    (no_update, *parametrize_constants, cqm_placeholder),
    ("num_legs", *parametrize_constants, cqm_placeholder)]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.cqm_to_display", mock_print)
def test_cqm_generation(trigger, changed_input_val, problem_print_code_val, max_leg_slope_val,
    max_cost_val, max_time_val, weight_cost_val, weight_time_val, weight_slope_val,
    weight_cost_hardsoft_val, weight_time_hardsoft_val, weight_slope_hardsoft_val,
    weight_cost_penalty_val, weight_time_penalty_val, weight_slope_penalty_val,
    locomotion_val, cqm_print_val):
    """Test that a CQM is generated based on input signals."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{trigger}.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_hardsoft.get(), weight_time_hardsoft.get(), \
            weight_slope_hardsoft.get(), weight_cost_penalty.get(), \
            weight_time_penalty.get(), weight_slope_penalty.get(), \
            locomotion_state.get())

    changed_input.set(vars()["changed_input_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs + names_weight_inputs:
        globals()[key].set(vars()[key + "_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_val"])
    locomotion_state.set(locomotion_val)

    ctx = copy_context()

    output = ctx.run(run_callback)

    if trigger == "changed_input":
        assert type(output) == dimod.ConstrainedQuadraticModel
    if trigger == "problem_print_code":
        assert type(output) == dimod.ConstrainedQuadraticModel
    if trigger == no_update:
        assert output == no_update
    if trigger == "num_legs":
        assert output == no_update

parametrize_names = parametrize_names.split("trigger,")[1]
parametrize_constants = ["num_legs", problem_print_placeholder, 8, 200, 20, 33, 44, 55]
parametrize_vals = []
hardsoft = [h for h in product(["soft", "hard"], repeat=3)]
penalty = [p for p in product(["linear", "quadratic"], repeat=3)]
for h, p in zip(hardsoft, penalty):
    parametrize_vals.append(tuple([*parametrize_constants, *h, *p, locomotion_json,
        cqm_placeholder]))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.cqm_to_display", mock_print)
def test_cqm_weights(changed_input_val, problem_print_code_val, max_leg_slope_val,
    max_cost_val, max_time_val, weight_cost_val, weight_time_val, weight_slope_val,
    weight_cost_hardsoft_val, weight_time_hardsoft_val, weight_slope_hardsoft_val,
    weight_cost_penalty_val, weight_time_penalty_val, weight_slope_penalty_val,
    locomotion_val, cqm_print_val):
    """Test that CQM incorporates penalties correctly."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "changed_input.value"},
                {"prop_id": "problem_print_code.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_hardsoft.get(), weight_time_hardsoft.get(), \
            weight_slope_hardsoft.get(), weight_cost_penalty.get(), \
            weight_time_penalty.get(), weight_slope_penalty.get(), \
            locomotion_state.get())

    changed_input.set(vars()["changed_input_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs + names_weight_inputs:
        globals()[key].set(vars()[key + "_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_val"])
    locomotion_state.set(locomotion_val)

    ctx = copy_context()

    output = ctx.run(run_callback)

    if weight_cost_hardsoft_val == "soft":
        assert output._soft["Total cost"] == dimod.constrained.SoftConstraint(weight=weight_cost_val,
            penalty=weight_cost_penalty_val)
    else:
        with pytest.raises(Exception):
            output.constraint["Total cost"] == dimod.constrained.SoftConstraint(weight=weight_cost_val,
                penalty=weight_cost_penalty_val)
