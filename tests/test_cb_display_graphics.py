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

from formatting import sampleset_to_json, state_to_json, tour_to_json

from app import display_graphics

solutions_print_code = ContextVar("solutions_print_code")
problem_print_code = ContextVar("problem_print_code")
locomotion_state = ContextVar("locomotion_state")

parametrize_names = "trigger, fig_space, fig_time, fig_feasiblity"
parametrize_vals = [
    ("problem_print_code", "bar", "bar", "bar"),
    ("solutions_print_code", "bar", "bar", "scatter3d"),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_display_graphics(locomotion_data_default, tour_data_default_2_legs,
    samplesets_feasible_infeasible, trigger, fig_space, fig_time, fig_feasiblity):
    """Test display of graphics."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": f"{trigger}.value"}],}))

        return display_graphics(solutions_print_code.get(), problem_print_code.get(), \
            locomotion_state.get())

    solutions_print_code.set(sampleset_to_json(samplesets_feasible_infeasible["feasible"]))
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    locomotion_state.set(state_to_json(locomotion_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[0].to_dict()["data"][0]["type"] == fig_space
    assert output[1].to_dict()["data"][0]["type"] == fig_time
    assert output[2].to_dict()["data"][0]["type"] == fig_feasiblity

    if trigger == "problem_print_code":
        pass # TODO: add more test for this one
