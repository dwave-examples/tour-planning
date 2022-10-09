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
from app import user_inputs

from formatting import tour_from_json
from tour_planning import leg_ranges, budget_ranges, weight_ranges
from tour_planning import weight_init_values

input_print_placeholder = "input_print_placeholder"

for key in names_leg_inputs + names_budget_inputs + names_weight_inputs:
        vars()[key] = ContextVar(f"{key}")
for key in names_weight_inputs:
    vars()[f"{key}_slider"] = ContextVar(f"{key}_slider")
for key in names_weight_inputs:
    vars()[f"{key}_radio"] = ContextVar(f"{key}_radio")

input_vals = [{"prop_id": f"{key}.value"} for key in
    names_leg_inputs + names_budget_inputs + names_weight_inputs]
input_vals.extend([{"prop_id": f"{key}_slider.value"} for key in
    names_weight_inputs])
input_vals.extend([{"prop_id": f"{key}_radio.value"} for key in
    names_weight_inputs])

parametrize_names = ", ".join([f'{key}_in ' for key in
        names_leg_inputs +  names_budget_inputs + names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_slider_in ' for key in names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_radio_in ' for key in names_weight_inputs]) + \
    ", input_print_val, " + \
    ", ".join([f'{key}_out ' for key in names_leg_inputs + names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_slider_out ' for key in names_weight_inputs])

parametrize_vals = []
for i in range(10):
    leg_vals = [random.randint(leg_ranges[key][0], leg_ranges[key][1])
        for key in names_leg_inputs]
    budget_vals = [random.randint(budget_ranges[key][0], budget_ranges[key][1])
        for key in names_budget_inputs]
    weight_vals = [random.randint(weight_ranges[key][0], 3*weight_init_values[key])
        for key in names_weight_inputs]
    radio_vals = random.choices(["soft", "hard"], k=3)
    an_input = []
    an_input.extend(leg_vals)
    an_input.extend(budget_vals)
    an_input.extend(weight_vals)
    an_input.extend(list(np.log10([w + 1 for w in weight_vals])))      # sliders
    an_input.extend(radio_vals)
    an_input.extend([input_print_placeholder])
    an_input.extend(leg_vals)
    an_input.extend(weight_vals)
    an_input.extend(list(np.log10([w + 1 for w in weight_vals])))
    parametrize_vals.append(tuple(an_input))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_user_inputs_expected_outputs(mocker, num_legs_in, max_leg_length_in, min_leg_length_in,
    max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in, weight_time_in,
    weight_slope_in, weight_cost_slider_in, weight_time_slider_in,
    weight_slope_slider_in, weight_cost_radio_in, weight_time_radio_in,
    weight_slope_radio_in, input_print_val, num_legs_out, max_leg_length_out,
    min_leg_length_out, max_leg_slope_out, weight_cost_out, weight_time_out,
    weight_slope_out, weight_cost_slider_out, weight_time_slider_out,
    weight_slope_slider_out):
    """Test that outputs are correctly updated from inputs."""

    untriggered = copy.deepcopy(input_vals)
    untriggered.remove({'prop_id': 'num_legs.value'})

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "num_legs.value"}],
            "input_values": untriggered}))

        return user_inputs(num_legs.get(), max_leg_length.get(), \
            min_leg_length.get(), max_leg_slope.get(), max_cost.get(), \
            max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_slider.get(), weight_time_slider.get(), \
            weight_slope_slider.get(), weight_cost_radio.get(), weight_time_radio.get(), \
            weight_slope_radio.get())

    for key in names_leg_inputs + names_budget_inputs + names_weight_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_slider"].set(vars()[f"{key}_radio_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_radio"].set(vars()[f"{key}_radio_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[1:] == (num_legs_in, max_leg_length_in, min_leg_length_in,
        max_leg_slope_in, weight_cost_in, weight_time_in, weight_slope_in,
        weight_cost_slider_in, weight_time_slider_in, weight_slope_slider_in)

triggers = [random.choice([*names_leg_inputs, *names_budget_inputs,
    *names_weight_inputs]) for i in range(10)]
parametrize_names_triggers = parametrize_names + ", triggers"
parametrize_vals_triggers = [(*parametrize_vals[0], triggers)]

@pytest.mark.parametrize(parametrize_names_triggers, parametrize_vals_triggers)
def test_user_inputs_print_last_change(mocker, num_legs_in, max_leg_length_in, min_leg_length_in,
    max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in, weight_time_in,
    weight_slope_in, weight_cost_slider_in, weight_time_slider_in,
    weight_slope_slider_in, weight_cost_radio_in, weight_time_radio_in,
    weight_slope_radio_in, input_print_val, num_legs_out, max_leg_length_out,
    min_leg_length_out, max_leg_slope_out, weight_cost_out, weight_time_out,
    weight_slope_out, weight_cost_slider_out, weight_time_slider_out,
    weight_slope_slider_out, triggers):
    """Test that triggered input is correctly identified & set in ``input_print``."""

    for test in triggers:
        untriggered = copy.deepcopy(input_vals)
        untriggered.remove({"prop_id": f"{test}.value"})

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": f"{test}.value"}],
            "input_values": untriggered}))

        return user_inputs(num_legs.get(), max_leg_length.get(), \
            min_leg_length.get(), max_leg_slope.get(), max_cost.get(), \
            max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_slider.get(), weight_time_slider.get(), \
            weight_slope_slider.get(), weight_cost_radio.get(), weight_time_radio.get(), \
            weight_slope_radio.get())

    for key in names_leg_inputs + names_budget_inputs + names_weight_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_slider"].set(vars()[f"{key}_radio_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_radio"].set(vars()[f"{key}_radio_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)
    find_changed = [line for line in output[0].split("\n") if "<<--" in line]
    assert test in find_changed[0]
