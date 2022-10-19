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

from app import display_locomotion

problem_print_code = ContextVar("problem_print_code")

problem_json = '[{"length": 5.3, "uphill": 7.0, "toll": false},'+\
'{"length": 5.6, "uphill": 2.9, "toll": false}]'

boundaries = {'cost_min': 0, 'cost_max': 54, 'cost_avg': 27, 'time_min': 2,
    'time_max': 11, 'time_avg': 3}

parametrize_vals = [
    (problem_json, boundaries),]

@pytest.mark.parametrize("problem_print_code_val, boundaries", parametrize_vals)
def test_display_locomotion(problem_print_code_val, boundaries):
    """Test display of locomotion modes."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "problem_print_code.value"}],}))

        return display_locomotion(problem_print_code.get())

    problem_print_code.set(problem_print_code_val)

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
