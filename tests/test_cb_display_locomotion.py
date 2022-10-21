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

from app import names_all_modes, names_locomotion_inputs
from app import display_locomotion

cqm_print = ContextVar("cqm_print")
problem_print_code = ContextVar("problem_print_code")
for key in names_locomotion_inputs:
    vars()[key] = ContextVar(f"{key}")
for key in names_all_modes:
    vars()[f"{key}_use"] = ContextVar(f"{key}_use")

state_vals = [{"prop_id": "problem_print_code.value"}]
state_vals.extend([{"prop_id": f"{key}.value"} for key in names_locomotion_inputs])
state_vals.extend([{"prop_id": f"{key}_use.value"} for key in names_all_modes])

problem_json = '[{"length": 5.3, "uphill": 7.0, "toll": false},'+\
'{"length": 5.6, "uphill": 2.9, "toll": false}]'

boundaries = {'cost_min': 0.0, 'cost_max': 54.5, 'cost_avg': 27.2, 'time_min': 1.6,
    'time_max': 10.9, 'time_avg': 2.7}

locomotion = {
    "walk": {"speed": 1, "cost": 0, "exercise": 1, "use": True},
    "cycle": {"speed": 3, "cost": 2, "exercise": 2, "use": True},
     "bus": {"speed": 4, "cost": 3, "exercise": 0, "use": True},
     "drive": {"speed": 7, "cost": 5, "exercise": 0, "use": True}}

locomotion_vals = [val for vals in locomotion.values() for
    val in vals.values() if not isinstance(val, bool)]
locomotion_use_vals = [val for vals in locomotion.values() for
    val in vals.values() if isinstance(val, bool)]

parametrize_names = "cqm_print_val, problem_print_code_val, " + \
    ", " + ", ".join([f'{key}_val ' for key in names_locomotion_inputs]) + \
    ", " + ", ".join([f'{key}_use_val ' for key in names_all_modes]) + \
    ", boundaries"

parametrize_vals = [
    (problem_json, problem_json, *locomotion_vals, *locomotion_use_vals,
        boundaries),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_display_locomotion(cqm_print_val, problem_print_code_val,
    walk_speed_val, walk_cost_val, walk_exercise_val,
    cycle_speed_val, cycle_cost_val, cycle_exercise_val,
    bus_speed_val, bus_cost_val, bus_exercise_val,
    drive_speed_val, drive_cost_val, drive_exercise_val,
    walk_use_val, cycle_use_val, bus_use_val, drive_use_val,
    boundaries):
    """Test display of locomotion modes."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "cqm_print.value"}],
            "state_values": state_vals}))

        return display_locomotion(cqm_print.get(), problem_print_code.get(),
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get(), \
            walk_use.get(), cycle_use.get(), bus_use.get(), drive_use.get())

    cqm_print.set(cqm_print_val)
    problem_print_code.set(problem_print_code_val)
    for key in names_locomotion_inputs:
        globals()[key].set(vars()[key + "_val"])
    for key in names_all_modes:
        globals()[f"{key}_use"].set(vars()[f"{key}_use_val"])

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
