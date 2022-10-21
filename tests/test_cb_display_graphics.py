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

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

import plotly

import dimod

from formatting import tour_from_json

from app import names_locomotion_inputs, names_all_modes
from app import display_graphics

solutions_print_code = ContextVar("solutions_print_code")
problem_print_code = ContextVar("problem_print_code")
for key in names_locomotion_inputs:
    vars()[key] = ContextVar(f"{key}")
for key in names_all_modes:
    vars()[f"{key}_use"] = ContextVar(f"{key}_use")

problem_json = '[{"length": 5.3, "uphill": 7.0, "toll": false},'+\
'{"length": 5.6, "uphill": 2.9, "toll": false}]'

sampleset = dimod.SampleSet.from_samples(dimod.as_samples([
    {"bus_0": 0, "drive_0": 1, "cycle_0": 0, "walk_0": 0,
        "bus_1": 0, "drive_1": 1, "cycle_1": 0, "walk_1": 0},
    {"bus_0": 0, "drive_0": 0, "cycle_0": 0, "walk_0": 1,
        "bus_1": 0, "drive_1": 1, "cycle_1": 0, "walk_1": 0}]), "BINARY", [0, 0])
sampleset = dimod.append_data_vectors(sampleset, is_satisfied=[[True], [True]])
sampleset = dimod.append_data_vectors(sampleset, is_feasible=[True, False])
sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
first = sorted({int(key.split("_")[1]): key.split("_")[0] for key,val in \
    sampleset_feasible.first.sample.items() if val==1.0}.items())
samples = {"sampleset": sampleset, "feasible": sampleset_feasible, "first": first}

locomotion = {
    "walk": {"speed": 1, "cost": 0, "exercise": 1, "use": True},
    "cycle": {"speed": 3, "cost": 2, "exercise": 2, "use": True},
     "bus": {"speed": 4, "cost": 3, "exercise": 0, "use": True},
     "drive": {"speed": 7, "cost": 5, "exercise": 0, "use": True}}

locomotion_vals = [val for vals in locomotion.values() for
    val in vals.values() if not isinstance(val, bool)]
locomotion_use_vals = [val for vals in locomotion.values() for
    val in vals.values() if isinstance(val, bool)]

parametrize_names = "trigger, solutions_print_code_val, problem_print_code_val, " + \
    ", " + ", ".join([f'{key}_val ' for key in names_locomotion_inputs]) + \
    ", " + ", ".join([f'{key}_use_val ' for key in names_all_modes]) + \
    ", fig_space, fig_time, fig_feasiblity"
parametrize_vals = [
    ("problem_print_code", "anything", problem_json, *locomotion_vals,
        *locomotion_use_vals, "bar", "bar", "bar"),
    ("solutions_print_code", samples, problem_json, *locomotion_vals,
        *locomotion_use_vals, "bar", "bar", "scatter3d"),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.sampleset_from_json", return_value=samples)
def test_display_graphics(mock, trigger, solutions_print_code_val, problem_print_code_val,
    walk_speed_val, walk_cost_val, walk_exercise_val,
    cycle_speed_val, cycle_cost_val, cycle_exercise_val,
    bus_speed_val, bus_cost_val, bus_exercise_val,
    drive_speed_val, drive_cost_val, drive_exercise_val,
    walk_use_val, cycle_use_val, bus_use_val, drive_use_val,
    fig_space, fig_time, fig_feasiblity):
    """Test display of graphics."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": f"{trigger}.value"}],}))

        return display_graphics(solutions_print_code.get(), problem_print_code.get(), \
            walk_speed.get(), walk_cost.get(), walk_exercise.get(),  \
            cycle_speed.get(), cycle_cost.get(), cycle_exercise.get(), \
            bus_speed.get(), bus_cost.get(), bus_exercise.get(), \
            drive_speed.get(), drive_cost.get(), drive_exercise.get(),
            walk_use.get(), cycle_use.get(), bus_use.get(), drive_use.get())

    solutions_print_code.set(solutions_print_code_val)
    problem_print_code.set(problem_print_code_val)
    for key in names_locomotion_inputs:
        globals()[key].set(vars()[key + "_val"])
    for key in names_all_modes:
        globals()[f"{key}_use"].set(vars()[f"{key}_use_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[0].to_dict()["data"][0]["type"] == fig_space
    assert output[1].to_dict()["data"][0]["type"] == fig_time
    assert output[2].to_dict()["data"][0]["type"] == fig_feasiblity

    if trigger == "problem_print_code":
        pass # TODO: add more test for this one
