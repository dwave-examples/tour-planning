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

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

from app import names_leg_inputs, names_budget_inputs, names_weight_inputs
from app import check_user_inputs

from formatting import tour_from_json
from tour_planning import leg_ranges, budget_ranges, weight_ranges
from tour_planning import weight_init_values

for key in names_leg_inputs + names_budget_inputs + names_weight_inputs:
        vars()[key] = ContextVar(f"{key}")
for key in names_weight_inputs:
    vars()[f"{key}_penalty"] = ContextVar(f"{key}_penalty")
for key in names_weight_inputs:
    vars()[f"{key}_hardsoft"] = ContextVar(f"{key}_hardsoft")

input_vals = [{"prop_id": f"{key}.value"} for key in
    names_leg_inputs + names_budget_inputs + names_weight_inputs]
input_vals.extend([{"prop_id": f"{key}_penalty.value"} for key in
    names_weight_inputs])
input_vals.extend([{"prop_id": f"{key}_hardsoft.value"} for key in
    names_weight_inputs])

parametrize_names = "trigger, " + ", ".join([f'{key}_in ' for key in
        names_leg_inputs +  names_budget_inputs + names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_penalty_in ' for key in names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_hardsoft_in ' for key in names_weight_inputs]) + \
    ", changed_input_out, max_leg_length_out, min_leg_length_out"

def leg_length(trigger, max_leg_length, min_leg_length):

    if trigger == "max_leg_length" and max_leg_length <= min_leg_length:
        return max_leg_length, max_leg_length
    if trigger == "min_leg_length" and min_leg_length >= max_leg_length:
        return min_leg_length, min_leg_length
    else:
        return max_leg_length, min_leg_length


parametrize_vals = []
for i in range(10):
    trigger = random.choice([*names_leg_inputs, *names_budget_inputs,
        *names_weight_inputs, *[f"{k}_penalty" for k in names_weight_inputs],
        *[f"{k}_hardsoft" for k in names_weight_inputs]])
    leg_vals = [random.randint(leg_ranges[key][0], leg_ranges[key][1])
        for key in names_leg_inputs]
    budget_vals = [random.randint(budget_ranges[key][0], budget_ranges[key][1])
        for key in names_budget_inputs]
    weight_vals = [random.randint(weight_ranges[key][0], 3*weight_init_values[key])
        for key in names_weight_inputs]
    penalty_vals = random.choices(["linear", "quadratic"], k=3)
    hardsoft_vals = random.choices(["soft", "hard"], k=3)
    an_input = [trigger, *leg_vals, *budget_vals, *weight_vals, *penalty_vals,
        *hardsoft_vals, trigger,
        *leg_length(trigger, leg_vals[1], leg_vals[2])]
    parametrize_vals.append(tuple(an_input))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_user_inputs_expected_outputs(trigger, num_legs_in, max_leg_length_in,
    min_leg_length_in, max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in,
    weight_time_in, weight_slope_in, weight_cost_penalty_in, weight_time_penalty_in,
    weight_slope_penalty_in, weight_cost_hardsoft_in, weight_time_hardsoft_in,
    weight_slope_hardsoft_in, changed_input_out, max_leg_length_out,
    min_leg_length_out):
    """Test triggering input sets ``changed_input`` and correct min/max leg length."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{trigger}.value"}],
            "input_values": input_vals}))

        return check_user_inputs(num_legs.get(), max_leg_length.get(), \
            min_leg_length.get(), max_leg_slope.get(), max_cost.get(), \
            max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_penalty.get(), weight_time_penalty.get(), \
            weight_slope_penalty.get(), weight_cost_hardsoft.get(), \
            weight_time_hardsoft.get(), weight_slope_hardsoft.get())

    for key in names_leg_inputs + names_budget_inputs + names_weight_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output == (trigger, max_leg_length_out, min_leg_length_out)
