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

btn_solve_cqm = ContextVar('btn_solve_cqm')

from app import alert_no_solver

@pytest.mark.parametrize("input_val, output_val",
    [(0, True), (1, True), (0, False), (1, False)])
def test_alert_no_solver(mocker, input_val, output_val):
    """Test that a failed cloud-client client is identified."""

    if output_val:
        mocker.patch('app.client', None)
    else:
        mocker.patch('app.client', "Henry")

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs":
            [{"prop_id": "btn_solve_cqm.n_clicks"}]}))

        return alert_no_solver(btn_solve_cqm.get())

    btn_solve_cqm.set(input_val)

    ctx = copy_context()

    output = ctx.run(run_callback)
    assert output == output_val
