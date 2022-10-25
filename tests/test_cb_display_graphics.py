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

from helpers.formatting import sampleset_to_json, state_to_json, tour_to_json

from app import display_graphics

solutions_print_code = ContextVar("solutions_print_code")
problem_print_code = ContextVar("problem_print_code")
locomotion_state = ContextVar("locomotion_state")

def test_display_graphics_feasible(locomotion_data_default, tour_data_default_2_legs,
    samplesets_feasible_infeasible):
    """Test data graphics generated for all three plot types."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "solutions_print_code.value"}],}))

        return display_graphics(solutions_print_code.get(), problem_print_code.get(), \
            locomotion_state.get())

    solutions_print_code.set(sampleset_to_json(samplesets_feasible_infeasible["feasible"]))
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    locomotion_state.set(state_to_json(locomotion_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output[0].data[0]) == plotly.graph_objs.Bar
    assert type(output[1].data[0]) == plotly.graph_objs.Bar
    assert type(output[2].data[0]) == plotly.graph_objs.Scatter3d

    assert len(output[0].data[0]["x"]) == 2
    assert len(output[1].data[0]["x"]) == 2
    assert len(output[1].data[0]["x"]) == 2

def test_display_graphics_infeasible(locomotion_data_default, tour_data_default_2_legs,
    samplesets_feasible_infeasible):
    """Test data graphics generated for only two plot types."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "solutions_print_code.value"}],}))

        return display_graphics(solutions_print_code.get(), problem_print_code.get(), \
            locomotion_state.get())

    solutions_print_code.set(sampleset_to_json(samplesets_feasible_infeasible["infeasible"]))
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    locomotion_state.set(state_to_json(locomotion_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output[0].data[0]) == plotly.graph_objs.Bar
    assert type(output[1].data[0]) == plotly.graph_objs.Bar
    assert type(output[2].data[0]) == plotly.graph_objs.Scatter3d

    assert len(output[0].data[0]["x"]) == 2
    not "x" in output[1].to_dict()["data"][0].keys()
    assert len(output[2].data[0]["x"]) == 2


def test_display_graphics_no_sampleset(locomotion_data_default, tour_data_default_2_legs):
    """Test data graphics generated for only two plot types when solver failed."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "solutions_print_code.value"}],}))

        return display_graphics(solutions_print_code.get(), problem_print_code.get(), \
            locomotion_state.get())

    solutions_print_code.set("samplesets_feasible_infeasible")
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    locomotion_state.set(state_to_json(locomotion_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output[0].data[0]) == plotly.graph_objs.Bar
    assert type(output[1].data[0]) == plotly.graph_objs.Bar
    assert type(output[2].data[0]) == plotly.graph_objs.Bar

    assert len(output[0].data[0]["x"]) == 2
    assert not "x" in output[1].to_dict()["data"][0].keys()
    assert not "x" in output[2].to_dict()["data"][0].keys()


def test_display_graphics_problem_print(locomotion_data_default, tour_data_default_2_legs,
    samplesets_feasible_infeasible):
    """Test empty graphics generated on problem print trigger."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "problem_print_code.value"}],}))

        return display_graphics(solutions_print_code.get(), problem_print_code.get(), \
            locomotion_state.get())

    solutions_print_code.set(sampleset_to_json(samplesets_feasible_infeasible["feasible"]))
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    locomotion_state.set(state_to_json(locomotion_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output[0].data[0]) == plotly.graph_objs.Bar
    assert type(output[1].data[0]) == plotly.graph_objs.Bar
    assert type(output[2].data[0]) == plotly.graph_objs.Bar

    assert len(output[0].data[0]["x"]) == 2
    assert not "x" in output[1].to_dict()["data"][0].keys()
    assert not "x" in output[2].to_dict()["data"][0].keys()
