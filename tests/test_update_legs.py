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

output_placeholder = " "

from app import names_leg_inputs, names_budget_inputs, names_weight_inputs
from app import update_legs
from formatting import tour_from_json

changed_input = ContextVar("changed_input")
for key in names_leg_inputs:
    vars()[key] = ContextVar(f"{key}")

states = [{"prop_id": f"{key}.value"} for key in names_leg_inputs]

output_placeholder = " "

parametrize_names = "changed_input_val, " + \
    ", ".join([f'{key}_val' for key in names_leg_inputs]) + \
    ", problem_print_code_val, problem_print_human_val"

parametrize_constant_vals = [(10, 10, 3, 8)]

parametrize_vals = []
for i in range(5):
    trigger = random.choice([*names_leg_inputs, *names_budget_inputs,
        *names_weight_inputs])
    output = output_placeholder if any(trigger == key for key in names_leg_inputs) else \
        no_update
    parametrize_vals.append((trigger, *parametrize_constant_vals[0], output, output))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_legs_generation_trigger(changed_input_val, num_legs_val,
    max_leg_length_val, min_leg_length_val, max_leg_slope_val,
    problem_print_code_val, problem_print_human_val):
    """Test that new legs are correctly generated only when needed."""

    print(f"tested for {changed_input_val}. {changed_input_val in names_leg_inputs}")

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{changed_input_val}.value"}],
            "state_values": states}))

        return update_legs(changed_input.get(), num_legs.get(), max_leg_length.get(),\
            min_leg_length.get(), max_leg_slope.get())

    changed_input.set(changed_input_val)
    for key in names_leg_inputs:
        globals()[key].set(vars()[f"{key}_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    print(f"output: {output}.")

    if not any(changed_input_val == key for key in names_leg_inputs):
        assert output == (no_update, no_update)
    else:
        assert len(tour_from_json(output[0])) == num_legs_val   # problem_print_code_val
