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

from helpers.formatting import state_to_json, state_from_json, tour_to_json

from app import names_budget_inputs

from app import generate_cqm

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

def mock_print(self):
    return self

parametrize_vals = [("changed_input", dimod.ConstrainedQuadraticModel()),
    ("problem_print_code", dimod.ConstrainedQuadraticModel()),
    (no_update, no_update),
    ("num_legs", no_update)]

@pytest.mark.parametrize("trigger, output_val", parametrize_vals)
@patch("app.formatting.cqm_to_display", mock_print)
def test_cqm_generation_trigger(locomotion_data_default, weight_data_default,
    tour_data_default_2_legs, trigger, output_val):
    """Test that a CQM is generated or not based on triggering input."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{trigger}.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weights_state.get(), \
            locomotion_state.get())

    changed_input.set("num_legs")
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    max_leg_slope.set(6)
    for key in names_budget_inputs:
        globals()[key].set(10)
    locomotion_state.set(state_to_json(locomotion_data_default))
    weights_state.set(state_to_json(weight_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output) == type(output_val)

parametrize_vals = []
hardsoft = [h for h in product(["soft", "hard"], repeat=3)]
penalty = [p for p in product(["linear", "quadratic"], repeat=3)]
for h, p in zip(hardsoft, penalty):
    weights_permutations = {
        "weight_cost":  {
            "weight": None if h[0] == "hard" else 33,
            "penalty": p[0]},
         "weight_time": {
            "weight": None if h[1] == "hard" else 44,
            "penalty": p[1]},
         "weight_slope": {
                "weight": None if h[2] == "hard" else 55,
                "penalty": p[2]}}
    parametrize_vals.append(tuple([weights_permutations, "dummy"]))
# seems parameterize doesn't like one-value tuples
@pytest.mark.parametrize("weights_in, dummy", parametrize_vals)
@patch("app.formatting.cqm_to_display", mock_print)
def test_cqm_generation_penalties(locomotion_data_default, tour_data_default_2_legs,
    weights_in, dummy):
    """Test that CQM incorporates penalties correctly."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "changed_input.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weights_state.get(), \
            locomotion_state.get())

    changed_input.set("num_legs")
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    max_leg_slope.set(6)
    for key in names_budget_inputs:
        globals()[key].set(10)
    locomotion_state.set(state_to_json(locomotion_data_default))
    weights_state.set(state_to_json(weights_in))

    ctx = copy_context()

    output = ctx.run(run_callback)

    weight_vals = weights_in

    if weight_vals["weight_cost"]["weight"] != None:
        assert output._soft["Total cost"] == dimod.constrained.SoftConstraint(
            weight=weight_vals["weight_cost"]["weight"],
            penalty=weight_vals["weight_cost"]["penalty"])
    else:
        with pytest.raises(Exception):
            output.constraint["Total cost"] == dimod.constrained.SoftConstraint(
                weight=weight_vals["weight_cost"]["weight"],
                penalty=weight_vals["weight_cost"]["penalty"])


def test_cqm_generation_locomotion(locomotion_data_default, weight_data_default,
    tour_data_simple):
    """Test that a CQM correctly uses locomotion values."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "changed_input.value"}],
            "state_values": state_vals}))

        return generate_cqm(changed_input.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weights_state.get(), \
            locomotion_state.get())

    changed_input.set("num_legs")
    problem_print_code.set(tour_to_json(tour_data_simple))
    max_leg_slope.set(6)
    for key in names_budget_inputs:
        globals()[key].set(10)
    locomotion_state.set(state_to_json(locomotion_data_default))
    weights_state.set(state_to_json(weight_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    lines = output.split("\n")
    assert "0.333333333" in lines[lines.index("Time Constraint: ") + 2]
    assert "0.25" in lines[lines.index("Time Constraint: ") + 2] 
