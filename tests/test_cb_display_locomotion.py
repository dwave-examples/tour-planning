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

from helpers.formatting import state_to_json, tour_to_json

from app import display_locomotion

cqm_print = ContextVar("cqm_print")
problem_print_code = ContextVar("problem_print_code")
locomotion_state = ContextVar("locomotion_state")

state_vals = [{"prop_id": "problem_print_code.value"}]
state_vals.extend([{"prop_id": "locomotion_state.children"}])

boundaries = {'cost_min': 0.0, 'cost_max': 54.5, 'cost_avg': 27.2, 'time_min': 1.6,
    'time_max': 10.9, 'time_avg': 2.7}

@pytest.mark.parametrize("cqm_print_val, boundaries", [("a CQM", boundaries),])
def test_display_locomotion(locomotion_data_default, tour_data_default_2_legs,
    cqm_print_val, boundaries):
    """Test display of locomotion modes."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "cqm_print.value"}],
            "state_values": state_vals}))

        return display_locomotion(cqm_print.get(), problem_print_code.get(),
            locomotion_state.get())

    cqm_print.set(cqm_print_val)
    problem_print_code.set(tour_to_json(tour_data_default_2_legs))
    locomotion_state.set(state_to_json(locomotion_data_default))

    ctx = copy_context()

    output = ctx.run(run_callback)

    lines = output.split("\n")
    assert lines[0].split("from ")[1] == \
        f"{boundaries['cost_min']} to {boundaries['cost_max']}."
    assert lines[1].split("from ")[1] == \
        f"{boundaries['time_min']} to {boundaries['time_max']}."
    assert lines[3].split("is ")[1] == \
        f"{boundaries['cost_avg']}."
    assert lines[4].split("is ")[1] == \
        f"{boundaries['time_avg']}."
