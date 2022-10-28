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

from itertools import product

from tour_planning import names_weight_inputs

from app import disable_weights

for key in names_weight_inputs:
    vars()[f"{key}_hardsoft"] = ContextVar(f"{key}_hardsoft")

parametrize_names = ", ".join([f'{key}_hardsoft_in ' for key in names_weight_inputs]) + \
    "," + ", ".join([f'{key}_disable_out ' for key in names_weight_inputs])

parametrize_vals = list(tuple(product(["hard", "soft"], repeat=3)))
parametrize_vals = [(t1, t2, t3, True if t1=="hard" else False, True if t2=="hard"
    else False, True if t3=="hard" else False, ) for (t1, t2, t3) in parametrize_vals]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_disable_weights(weight_cost_hardsoft_in, weight_time_hardsoft_in,
weight_slope_hardsoft_in, weight_cost_disable_out, weight_time_disable_out,
weight_slope_disable_out):
    """Test disabling weights when constraint is hard."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "weight_cost_hardsoft.value"}]}))

        return disable_weights(weight_cost_hardsoft.get(), weight_time_hardsoft.get(), \
            weight_slope_hardsoft.get())

    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_in"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[:3] == (weight_cost_disable_out, weight_time_disable_out,
    weight_slope_disable_out)
    if weight_cost_disable_out:
        assert output[3] == [
            {"label": "Linear", "value": "linear", "disabled": True},
            {"label": "Quadratic", "value": "quadratic", "disabled": True}]
    else:
        assert output[3] == [
            {"label": "Linear", "value": "linear", "disabled": False},
            {"label": "Quadratic", "value": "quadratic", "disabled": False}]
    assert output[6] == {"color": "white", "font-size": 12, "display": "flex"}
