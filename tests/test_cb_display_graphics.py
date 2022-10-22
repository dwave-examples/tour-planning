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

from formatting import locomotion_to_json, tour_from_json

from app import names_locomotion_inputs, names_all_modes
from app import display_graphics

solutions_print_code = ContextVar("solutions_print_code")
problem_print_code = ContextVar("problem_print_code")
locomotion_state = ContextVar("locomotion_state")

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

locomotion_json = locomotion_to_json({
    "walk": {"speed": 1, "cost": 0, "exercise": 1, "use": True},
    "cycle": {"speed": 3, "cost": 2, "exercise": 2, "use": True},
     "bus": {"speed": 4, "cost": 3, "exercise": 0, "use": True},
     "drive": {"speed": 7, "cost": 5, "exercise": 0, "use": True}})

parametrize_names = "trigger, solutions_print_code_val, problem_print_code_val, " + \
    "locomotion_val, fig_space, fig_time, fig_feasiblity"
parametrize_vals = [
    ("problem_print_code", "anything", problem_json, locomotion_json,
        "bar", "bar", "bar"),
    ("solutions_print_code", samples, problem_json, locomotion_json,
        "bar", "bar", "scatter3d"),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.sampleset_from_json", return_value=samples)
def test_display_graphics(mock, trigger, solutions_print_code_val, problem_print_code_val,
    locomotion_val, fig_space, fig_time, fig_feasiblity):
    """Test display of graphics."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": f"{trigger}.value"}],}))

        return display_graphics(solutions_print_code.get(), problem_print_code.get(), \
            locomotion_state.get())

    solutions_print_code.set(solutions_print_code_val)
    problem_print_code.set(problem_print_code_val)
    locomotion_state.set(locomotion_val)

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[0].to_dict()["data"][0]["type"] == fig_space
    assert output[1].to_dict()["data"][0]["type"] == fig_time
    assert output[2].to_dict()["data"][0]["type"] == fig_feasiblity

    if trigger == "problem_print_code":
        pass # TODO: add more test for this one
