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

from helpers.formatting import state_to_json, state_from_json

from app import names_budget_inputs

from app import generate_cqm

problem_print_placeholder = '[{"length": 9.4, "uphill": 0.1, "toll": false}, {"length": 6.9, "uphill": 2.5, "toll": false}]'

changed_input = ContextVar("changed_input")
problem_print_code = ContextVar("problem_print_code")
max_leg_slope = ContextVar("max_leg_slope")
for key in names_budget_inputs:
    vars()[key] = ContextVar(f"{key}")
weights_state = ContextVar("weights_state")
locomotion_state = ContextVar("locomotion_state")

state_vals = [{"prop_id": "max_leg_slope"}]
state_vals.extend([{"prop_id": f"{key}.value"} for key in names_budget_inputs])
state_vals.extend([{"prop_id": "weights_state.children"}])
state_vals.extend([{"prop_id": "locomotion_state.children"}])

cqm_placeholder = " "

def mock_print(self):
    return self

weights_json = state_to_json({"weight_cost":  {"weight": None, "penalty": "linear"},
     "weight_time": {"weight": None, "penalty": "linear"},
     "weight_slope": {"weight": 55, "penalty": "quadratic"}})

parametrize_names = "trigger, changed_input_val, problem_print_code_val, max_leg_slope_val, " + \
    ", ".join([f'{key}_val ' for key in names_budget_inputs]) + \
    ", weights_val, cqm_print_val"

parametrize_constants = ["num_legs", problem_print_placeholder, 8, 200, 20,
    weights_json]
parametrize_vals = [("changed_input", *parametrize_constants, cqm_placeholder),
    ("problem_print_code", *parametrize_constants, cqm_placeholder),
    (no_update, *parametrize_constants, cqm_placeholder),
    ("num_legs", *parametrize_constants, cqm_placeholder)]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.cqm_to_display", mock_print)
def test_cqm_generation(locomotion_data_default, trigger, changed_input_val,
    problem_print_code_val, max_leg_slope_val, max_cost_val, max_time_val,
    weights_val, cqm_print_val):
    """Test that a CQM is generated based on input signals."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{trigger}.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weights_state.get(), \
            locomotion_state.get())

    changed_input.set(vars()["changed_input_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs:
        globals()[key].set(vars()[key + "_val"])
    locomotion_state.set(state_to_json(locomotion_data_default))
    weights_state.set(weights_val)

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
parametrize_constants = ["num_legs", problem_print_placeholder, 8, 200, 20]
parametrize_vals = []
hardsoft = [h for h in product(["soft", "hard"], repeat=3)]
penalty = [p for p in product(["linear", "quadratic"], repeat=3)]
for h, p in zip(hardsoft, penalty):
    weights_json = state_to_json({
        "weight_cost":  {
            "weight": None if h[0] == "hard" else 33,
            "penalty": p[0]},
         "weight_time": {
            "weight": None if h[1] == "hard" else 44,
            "penalty": p[1]},
         "weight_slope": {
                "weight": None if h[2] == "hard" else 55,
                "penalty": p[2]}})
    parametrize_vals.append(tuple([*parametrize_constants, weights_json,
        cqm_placeholder]))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.cqm_to_display", mock_print)
def test_cqm_weights(locomotion_data_default, changed_input_val,
    problem_print_code_val, max_leg_slope_val, max_cost_val, max_time_val,
    weights_val, cqm_print_val):
    """Test that CQM incorporates penalties correctly."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "changed_input.value"},
                {"prop_id": "problem_print_code.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weights_state.get(), locomotion_state.get())

    changed_input.set(vars()["changed_input_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs:
        globals()[key].set(vars()[key + "_val"])
    weights_state.set(weights_val)
    locomotion_state.set(state_to_json(locomotion_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    weight_vals = state_from_json(weights_val)

    if weight_vals["weight_cost"]["weight"] != None:
        assert output._soft["Total cost"] == dimod.constrained.SoftConstraint(
            weight=weight_vals["weight_cost"]["weight"],
            penalty=weight_vals["weight_cost"]["penalty"])
    else:
        with pytest.raises(Exception):
            output.constraint["Total cost"] == dimod.constrained.SoftConstraint(
                weight=weight_vals["weight_cost"]["weight"],
                penalty=weight_vals["weight_cost"]["penalty"])
