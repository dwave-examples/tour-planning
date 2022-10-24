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
from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

from parameterized import parameterized
import pytest

from itertools import product
import random

from helpers.formatting import state_to_json
from tour_planning import (leg_ranges, slope_ranges, budget_ranges, weight_ranges,
    weight_init_values)

from app import (names_all_modes, names_locomotion_inputs, names_leg_inputs,
    names_slope_inputs, names_budget_inputs, names_weight_inputs)

from app import check_user_inputs

for key in names_locomotion_inputs + names_leg_inputs + names_slope_inputs + \
    names_budget_inputs + names_weight_inputs:
        vars()[key] = ContextVar(f"{key}")
for key in names_weight_inputs:
    vars()[f"{key}_penalty"] = ContextVar(f"{key}_penalty")
for key in names_weight_inputs:
    vars()[f"{key}_hardsoft"] = ContextVar(f"{key}_hardsoft")
for key in names_all_modes:
    vars()[f"{key}_use"] = ContextVar(f"{key}_use")

input_vals = [{"prop_id": f"{key}.value"} for key in
    names_locomotion_inputs + names_leg_inputs + names_slope_inputs +
    names_budget_inputs + names_weight_inputs]
input_vals.extend([{"prop_id": f"{key}_penalty.value"} for key in
    names_weight_inputs])
input_vals.extend([{"prop_id": f"{key}_hardsoft.value"} for key in
    names_weight_inputs])
input_vals.extend([{"prop_id": f"{key}_use.value"} for key in
    names_all_modes])

def leg_length(trigger, max_leg_length, min_leg_length):

    if trigger == "max_leg_length" and max_leg_length <= min_leg_length:
        return max_leg_length, max_leg_length
    if trigger == "min_leg_length" and min_leg_length >= max_leg_length:
        return min_leg_length, min_leg_length
    else:
        return max_leg_length, min_leg_length

def get_locomotion_out(walk_speed_in, walk_cost_in, walk_exercise_in, walk_use_in,
    cycle_speed_in, cycle_cost_in, cycle_exercise_in, cycle_use_in, bus_speed_in,
    bus_cost_in, bus_exercise_in, bus_use_in, drive_speed_in, drive_cost_in,
    drive_exercise_in, drive_use_in):

    return state_to_json(
        {"walk":  {"speed": walk_speed_in, "cost": walk_cost_in, "exercise": walk_exercise_in,
            "use": walk_use_in},
        "cycle": {"speed": cycle_speed_in, "cost": cycle_cost_in, "exercise": cycle_exercise_in,
            "use": cycle_use_in},
        "bus": {"speed": bus_speed_in, "cost": bus_cost_in, "exercise": bus_exercise_in,
            "use": bus_use_in},
        "drive": {"speed": drive_speed_in, "cost": drive_cost_in, "exercise": drive_exercise_in,
            "use": drive_use_in}})

def get_weights_out(weight_cost_in, weight_cost_hardsoft_in, weight_cost_penalty_in,
    weight_time_in, weight_time_hardsoft_in, weight_time_penalty_in, weight_slope_in,
    weight_slope_hardsoft_in, weight_slope_penalty_in):

    return state_to_json(
        {"weight_cost":  {
            "weight": None if weight_cost_hardsoft_in == "hard" else weight_cost_in,
            "penalty": weight_cost_penalty_in},
         "weight_time": {
            "weight": None if weight_time_hardsoft_in == "hard" else weight_time_in,
            "penalty": weight_time_penalty_in},
         "weight_slope": {
            "weight": None if weight_slope_hardsoft_in == "hard" else weight_slope_in,
            "penalty": weight_slope_penalty_in}})

parametrize_names = "trigger, " + ", ".join([f'{key}_in ' for key in
        names_leg_inputs +  names_slope_inputs + \
        names_budget_inputs + names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_penalty_in ' for key in names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_hardsoft_in ' for key in names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_in ' for key in names_locomotion_inputs]) + \
    ", " + ", ".join([f'{key}_use_in ' for key in names_all_modes])

leg_vals = [val[0] for val in leg_ranges.values()]
slope_vals = [val[0] for val in slope_ranges.values()]
budget_vals = [val[0] for val in budget_ranges.values()]
weight_vals = [val[0] for val in weight_ranges.values()]
penalty_vals = ["linear", "quadratic", "linear"]
hardsoft_vals = ["soft", "hard", "soft"]
locomotion_vals = [2]*len(names_locomotion_inputs)
use_vals = [True]*len(names_all_modes)

parametrize_vals = []

for trigger in [*names_leg_inputs, *names_slope_inputs, *names_budget_inputs,
    *names_weight_inputs, *[f"{k}_penalty" for k in names_weight_inputs],
    *[f"{k}_hardsoft" for k in names_weight_inputs],
    *[key for key in names_locomotion_inputs], *[key for key in names_all_modes]]:
    an_input = [trigger, *leg_vals, *slope_vals, *budget_vals, *weight_vals,
        *penalty_vals, *hardsoft_vals, *locomotion_vals, *use_vals]
    parametrize_vals.append(tuple(an_input))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_user_inputs_generates_correct_changed_input(trigger, num_legs_in, max_leg_length_in,
    min_leg_length_in, max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in,
    weight_time_in, weight_slope_in, weight_cost_penalty_in, weight_time_penalty_in,
    weight_slope_penalty_in, weight_cost_hardsoft_in, weight_time_hardsoft_in,
    weight_slope_hardsoft_in,
    walk_speed_in, walk_cost_in, walk_exercise_in,
    cycle_speed_in, cycle_cost_in, cycle_exercise_in,
    bus_speed_in, bus_cost_in, bus_exercise_in,
    drive_speed_in, drive_cost_in, drive_exercise_in,
    walk_use_in, cycle_use_in, bus_use_in, drive_use_in):
    """Test triggering input sets correct ``changed_input``."""

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
            weight_time_hardsoft.get(), weight_slope_hardsoft.get(), \
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get(),
            walk_use.get(), cycle_use.get(), bus_use.get(), drive_use.get())

    for key in names_leg_inputs + names_slope_inputs + names_budget_inputs +  \
        names_weight_inputs + names_locomotion_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_in"])
    for key in names_all_modes:
        globals()[f"{key}_use"].set(vars()[f"{key}_use_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[0] == trigger

leg_vals_permutations = [[1, leg_ranges["max_leg_length"][0], leg_ranges["min_leg_length"][0]],
    [1, leg_ranges["max_leg_length"][1], leg_ranges["min_leg_length"][1]],
    [1, leg_ranges["max_leg_length"][0], leg_ranges["min_leg_length"][1]],
    [1, leg_ranges["max_leg_length"][1], leg_ranges["min_leg_length"][0]],
    [1, leg_ranges["max_leg_length"][0],
        random.randint(leg_ranges["min_leg_length"][0], leg_ranges["min_leg_length"][1])],
    [1, random.randint(leg_ranges["max_leg_length"][0], leg_ranges["max_leg_length"][1]),
        leg_ranges["min_leg_length"][1]],
    [1, leg_ranges["max_leg_length"][1],
        random.randint(leg_ranges["min_leg_length"][0], leg_ranges["min_leg_length"][1])],
    [1, random.randint(leg_ranges["max_leg_length"][0], leg_ranges["max_leg_length"][1]),
    leg_ranges["min_leg_length"][0]]]
trigger_vals = ["max_leg_length", "min_leg_length"]

parametrize_vals = []
for trigger in trigger_vals:
    for leg_val in leg_vals_permutations:
        an_input = [trigger, *leg_val, *slope_vals, *budget_vals, *weight_vals,
            *penalty_vals, *hardsoft_vals, *locomotion_vals, *use_vals]
        parametrize_vals.append(tuple(an_input))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_user_inputs_max_min_leg_length(trigger, num_legs_in, max_leg_length_in,
    min_leg_length_in, max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in,
    weight_time_in, weight_slope_in, weight_cost_penalty_in, weight_time_penalty_in,
    weight_slope_penalty_in, weight_cost_hardsoft_in, weight_time_hardsoft_in,
    weight_slope_hardsoft_in,
    walk_speed_in, walk_cost_in, walk_exercise_in,
    cycle_speed_in, cycle_cost_in, cycle_exercise_in,
    bus_speed_in, bus_cost_in, bus_exercise_in,
    drive_speed_in, drive_cost_in, drive_exercise_in,
    walk_use_in, cycle_use_in, bus_use_in, drive_use_in):
    """Test correct min/max leg length."""

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
            weight_time_hardsoft.get(), weight_slope_hardsoft.get(), \
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get(),
            walk_use.get(), cycle_use.get(), bus_use.get(), drive_use.get())

    for key in names_leg_inputs + names_slope_inputs + names_budget_inputs +  \
        names_weight_inputs + names_locomotion_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_in"])
    for key in names_all_modes:
        globals()[f"{key}_use"].set(vars()[f"{key}_use_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[1] >= output[2]

use_vals_permutations = [f"{mode}_use" for mode in names_all_modes]
parametrize_vals = []
for trigger in trigger_vals:
    for use_val in product([True, False], repeat=len(names_all_modes)):
        an_input =  [trigger, *leg_vals, *slope_vals, *budget_vals, *weight_vals,
            *penalty_vals, *hardsoft_vals, *locomotion_vals, *use_val]
        parametrize_vals.append(tuple(an_input))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_user_inputs_use_modes(trigger, num_legs_in, max_leg_length_in,
    min_leg_length_in, max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in,
    weight_time_in, weight_slope_in, weight_cost_penalty_in, weight_time_penalty_in,
    weight_slope_penalty_in, weight_cost_hardsoft_in, weight_time_hardsoft_in,
    weight_slope_hardsoft_in,
    walk_speed_in, walk_cost_in, walk_exercise_in,
    cycle_speed_in, cycle_cost_in, cycle_exercise_in,
    bus_speed_in, bus_cost_in, bus_exercise_in,
    drive_speed_in, drive_cost_in, drive_exercise_in,
    walk_use_in, cycle_use_in, bus_use_in, drive_use_in):
    """Test correct use of locomotion modes."""

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
            weight_time_hardsoft.get(), weight_slope_hardsoft.get(), \
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get(),
            walk_use.get(), cycle_use.get(), bus_use.get(), drive_use.get())

    for key in names_leg_inputs + names_slope_inputs + names_budget_inputs +  \
        names_weight_inputs + names_locomotion_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_in"])
    for key in names_all_modes:
        globals()[f"{key}_use"].set(vars()[f"{key}_use_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    if any([walk_use_in, cycle_use_in, bus_use_in, drive_use_in]):
        assert output[3:3+len(names_all_modes)] == tuple([walk_use_in, cycle_use_in,
            bus_use_in, drive_use_in])
    else:
        assert not all(output[3:3+len(names_all_modes)])

locomotion_vals_random = [random.randint(1, 100) for key in names_locomotion_inputs]
parametrize_vals = [("num_legs", *leg_vals, *slope_vals, *budget_vals, *weight_vals,
        *penalty_vals, *hardsoft_vals, *locomotion_vals_random, *use_vals)]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_user_inputs_locomotion_json(trigger, num_legs_in, max_leg_length_in,
    min_leg_length_in, max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in,
    weight_time_in, weight_slope_in, weight_cost_penalty_in, weight_time_penalty_in,
    weight_slope_penalty_in, weight_cost_hardsoft_in, weight_time_hardsoft_in,
    weight_slope_hardsoft_in,
    walk_speed_in, walk_cost_in, walk_exercise_in,
    cycle_speed_in, cycle_cost_in, cycle_exercise_in,
    bus_speed_in, bus_cost_in, bus_exercise_in,
    drive_speed_in, drive_cost_in, drive_exercise_in,
    walk_use_in, cycle_use_in, bus_use_in, drive_use_in):
    """Test correct saving of locomotion values."""

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
            weight_time_hardsoft.get(), weight_slope_hardsoft.get(), \
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get(),
            walk_use.get(), cycle_use.get(), bus_use.get(), drive_use.get())

    for key in names_leg_inputs + names_slope_inputs + names_budget_inputs +  \
        names_weight_inputs + names_locomotion_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_in"])
    for key in names_all_modes:
        globals()[f"{key}_use"].set(vars()[f"{key}_use_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[-2] == get_locomotion_out(walk_speed_in, walk_cost_in, walk_exercise_in, walk_use_in,
        cycle_speed_in, cycle_cost_in, cycle_exercise_in, cycle_use_in, bus_speed_in,
        bus_cost_in, bus_exercise_in, bus_use_in, drive_speed_in, drive_cost_in,
        drive_exercise_in, drive_use_in)

parametrize_vals = []
weight_vals_random = [int(random.random()*val[1]) for val in weight_ranges.values()]
for hardsoft in product(["hard", "soft"], repeat=3):
    an_input =  ["num_legs", *leg_vals, *slope_vals, *budget_vals, *weight_vals_random,
        *penalty_vals, *hardsoft, *locomotion_vals, *use_val]
    parametrize_vals.append(tuple(an_input))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_user_inputs_weights_json(trigger, num_legs_in, max_leg_length_in,
    min_leg_length_in, max_leg_slope_in, max_cost_in, max_time_in, weight_cost_in,
    weight_time_in, weight_slope_in, weight_cost_penalty_in, weight_time_penalty_in,
    weight_slope_penalty_in, weight_cost_hardsoft_in, weight_time_hardsoft_in,
    weight_slope_hardsoft_in,
    walk_speed_in, walk_cost_in, walk_exercise_in,
    cycle_speed_in, cycle_cost_in, cycle_exercise_in,
    bus_speed_in, bus_cost_in, bus_exercise_in,
    drive_speed_in, drive_cost_in, drive_exercise_in,
    walk_use_in, cycle_use_in, bus_use_in, drive_use_in):
    """Test correct saving of locomotion values."""

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
            weight_time_hardsoft.get(), weight_slope_hardsoft.get(), \
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get(),
            walk_use.get(), cycle_use.get(), bus_use.get(), drive_use.get())

    for key in names_leg_inputs + names_slope_inputs + names_budget_inputs +  \
        names_weight_inputs + names_locomotion_inputs:
            globals()[key].set(vars()[key + "_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_in"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_in"])
    for key in names_all_modes:
        globals()[f"{key}_use"].set(vars()[f"{key}_use_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[-1] == get_weights_out(weight_cost_in, weight_cost_hardsoft_in, weight_cost_penalty_in,
        weight_time_in, weight_time_hardsoft_in, weight_time_penalty_in, weight_slope_in,
        weight_slope_hardsoft_in, weight_slope_penalty_in)
