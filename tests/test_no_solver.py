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

import os
import sys
from parameterized import parameterized
import pytest

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict

sys.path.insert(0, os.path.abspath('.'))
sys.path.append(os.path.abspath('../'))

btn_solve_cqm = ContextVar('btn_solve_cqm')

import app

@pytest.mark.parametrize("input_val, output_val",
    [(0, True), (1, True)])
def test_no_solver_no_solver(mocker, input_val, output_val):
    mocker.patch.object(app, 'client', None)

    def run_callback():
            context_value.set(AttributeDict(**{"triggered_inputs":
                [{"prop_id": "btn_solve_cqm.n_clicks"}]}))
            return app.no_solver(btn_solve_cqm.get())

    btn_solve_cqm.set(input_val)

    ctx = copy_context()

    output = ctx.run(run_callback)
    assert output == output_val

@pytest.mark.parametrize("input_val, output_val",
    [(0, False), (1, False)])
def test_no_solver_with_solver(mocker, input_val, output_val):
    mocker.patch.object(app, 'client', "Henry")

    def run_callback():
            context_value.set(AttributeDict(**{"triggered_inputs":
                [{"prop_id": "btn_solve_cqm.n_clicks"}]}))
            return app.no_solver(btn_solve_cqm.get())

    btn_solve_cqm.set(input_val)

    ctx = copy_context()

    output = ctx.run(run_callback)
    assert output == output_val
