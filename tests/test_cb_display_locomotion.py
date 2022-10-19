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

import plotly

import dimod

from app import names_locomotion_inputs
from app import display_locomotion

problem_print_code = ContextVar("problem_print_code")
for key in names_locomotion_inputs:
    vars()[key] = ContextVar(f"{key}")

state_vals = [{"prop_id": f"{key}.value"} for key in names_locomotion_inputs]

problem_json = '[{"length": 5.3, "uphill": 7.0, "toll": false},'+\
'{"length": 5.6, "uphill": 2.9, "toll": false}]'

boundaries = {'cost_min': 0, 'cost_max': 54, 'cost_avg': 27, 'time_min': 2,
    'time_max': 11, 'time_avg': 3}

locomotion_vals = {"walk": [1, 0, 1],
"cycle": [3, 2, 2],
"bus": [4, 3, 0],
"drive": [7, 5, 0]}
locomotion_vals = [val for vals in locomotion_vals.values() for val in vals]

parametrize_names = "problem_print_code_val, " + \
    ", " + ", ".join([f'{key}_val ' for key in names_locomotion_inputs]) + \
    ", boundaries"

parametrize_vals = [
    (problem_json, *locomotion_vals, boundaries),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_display_locomotion(problem_print_code_val,
    walk_speed_val, walk_cost_val, walk_exercise_val,
    cycle_speed_val, cycle_cost_val, cycle_exercise_val,
    bus_speed_val, bus_cost_val, bus_exercise_val,
    drive_speed_val, drive_cost_val, drive_exercise_val,
    boundaries):
    """Test display of locomotion modes."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "problem_print_code.value"}],
            "state_values": state_vals}))

        return display_locomotion(problem_print_code.get(),
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get())

    problem_print_code.set(problem_print_code_val)
    for key in names_locomotion_inputs:
        globals()[key].set(vars()[key + "_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)
    print(output)

    lines = output.split("\n")
    assert lines[0].split("from ")[1] == \
        f"{boundaries['cost_min']} to {boundaries['cost_max']}."
    assert lines[1].split("from ")[1] == \
        f"{boundaries['time_min']} to {boundaries['time_max']}."
    assert lines[3].split("is ")[1] == \
        f"{boundaries['cost_avg']}."
    assert lines[4].split("is ")[1] == \
        f"{boundaries['time_avg']}."
