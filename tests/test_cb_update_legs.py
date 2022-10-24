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

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

import random

from helpers.formatting import tour_from_json, tour_to_display

from app import names_leg_inputs, names_budget_inputs, names_weight_inputs

from app import update_legs

changed_input = ContextVar("changed_input")
for key in names_leg_inputs:
    vars()[key] = ContextVar(f"{key}")
tollbooths_active = ContextVar("tollbooths_active")

states = [{"prop_id": f"{key}.value"} for key in names_leg_inputs]
states.extend([{"prop_id": "tollbooths_active.value"}])

parametrize_names = "changed_input_val, " + \
    ", ".join([f'{key}_val' for key in names_leg_inputs]) + \
    ", tollbooths_active_val, problem_print_code_val, problem_print_human_val"

parametrize_vals = []
for i in range(10):
    trigger = random.choice([*names_leg_inputs, *names_budget_inputs,
        *names_weight_inputs])
    output = " " if any(trigger == key for key in names_leg_inputs) else \
        no_update
    parametrize_vals.append((trigger, 10, 10, 3, True, output, output))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_legs_generation_trigger(changed_input_val, num_legs_val,
    max_leg_length_val, min_leg_length_val, tollbooths_active_val,
    problem_print_code_val, problem_print_human_val):
    """Test that new legs are correctly generated only when needed."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{changed_input_val}.value"}],
            "state_values": states}))

        return update_legs(changed_input.get(), num_legs.get(), max_leg_length.get(),\
            min_leg_length.get(), tollbooths_active.get())

    changed_input.set(changed_input_val)
    for key in names_leg_inputs:
        globals()[key].set(vars()[f"{key}_val"])
    tollbooths_active.set(tollbooths_active_val)

    ctx = copy_context()

    output = ctx.run(run_callback)

    if not any(changed_input_val == key for key in names_leg_inputs):
        assert output == (no_update, no_update)
    else:
        assert len(tour_from_json(output[0])) == num_legs_val   # problem_print_code_val

parametrize_names = "changed_input_val, " + \
    ", ".join([f'{key}_val' for key in names_leg_inputs]) + \
    ", tollbooths_active_val"
parametrize_vals = [("num_legs", 1, 10, 10, True)]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_legs_output(changed_input_val, num_legs_val,
    max_leg_length_val, min_leg_length_val, tollbooths_active_val):
    """Test that output is correctly generated."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "num_legs.value"}],
            "state_values": states}))

        return update_legs(changed_input.get(), num_legs.get(), max_leg_length.get(),\
            min_leg_length.get(), tollbooths_active.get())

    changed_input.set(changed_input_val)
    for key in names_leg_inputs:
        globals()[key].set(vars()[f"{key}_val"])
    tollbooths_active.set(tollbooths_active_val)

    ctx = copy_context()

    output = ctx.run(run_callback)
    problem_print_code_val = tour_from_json(output[0])
    problem_print_human_val = output[1]

    assert problem_print_code_val[0]["length"] == max_leg_length_val

    assert problem_print_human_val == tour_to_display(problem_print_code_val)
