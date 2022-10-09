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
from dash import no_update

from formatting import tour_from_json

import app

in_print = """
Configurable inputs have these supported ranges and current values:
"""

in_print_code = """[{"length": 2.6, "uphill": 7.1, "toll": true}, {"length": 8.3, "uphill": 5.3, "toll": true}, {"length": 5.8, "uphill": 1.1, "toll": false}, {"length": 5.0, "uphill": 0.1, "toll": false}, {"length": 8.5, "uphill": 4.4, "toll": false}, {"length": 9.2, "uphill": 3.1, "toll": false}, {"length": 7.3, "uphill": 4.8, "toll": false}, {"length": 7.4, "uphill": 0.3, "toll": false}, {"length": 3.9, "uphill": 4.7, "toll": false}, {"length": 4.2, "uphill": 4.3, "toll": false}]"""

input_print = ContextVar("input_print")
problem_print_code = ContextVar("problem_print_code")
max_leg_slope = ContextVar("max_leg_slope")
for key in app.names_budget_inputs + app.names_weight_inputs:
    vars()[key] = ContextVar(f"{key}")
for key in app.names_weight_inputs:
    vars()[f"{key}_radio"] = ContextVar(f"{key}_radio")

state_vals = [{"prop_id": "max_leg_slope"}]
state_vals.extend([{"prop_id": f"{key}.value"} for key in
    app.names_budget_inputs + app.names_weight_inputs])
state_vals.extend([{"prop_id": f"{key}_radio.value"} for key in app.names_weight_inputs])

cqm_placeholder = ""

def mock_print(self):
    return self

@pytest.mark.parametrize("input_print_val, problem_print_code_val, max_leg_slope_val, " +
    ", ".join([f'{key}_val ' for key in app.names_budget_inputs + app.names_weight_inputs]) +
    ", " + ", ".join([f'{key}_radio_val ' for key in app.names_weight_inputs]) +
    ", cqm_print_val",
    [(in_print, in_print_code, 8, 200, 20, 33, 44, 55, "soft", "soft", "hard", cqm_placeholder),
    (in_print, in_print_code, 5, 100, 54, 18, 66, 93, "hard", "soft", "soft", cqm_placeholder)])
def test_cqm(mocker, input_print_val, problem_print_code_val, max_leg_slope_val,
    max_cost_val, max_time_val, weight_cost_val, weight_time_val, weight_slope_val,
    weight_cost_radio_val, weight_time_radio_val, weight_slope_radio_val,
    cqm_print_val):

    mocker.patch.object(app.dimod.ConstrainedQuadraticModel, '__str__', mock_print)

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "input_print.value"},
                {"prop_id": "problem_print_code.value"}],
            "state_values": state_vals}))

        return app.cqm(input_print.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_radio.get(), weight_time_radio.get(), \
            weight_slope_radio.get())

    input_print.set(vars()["input_print_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in app.names_budget_inputs + app.names_weight_inputs:
        globals()[key].set(vars()[key + "_val"])
    for key in app.names_weight_inputs:
        globals()[f"{key}_radio"].set(vars()[f"{key}_radio_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output) == app.dimod.ConstrainedQuadraticModel
    assert type(output.constraints["One-hot leg0"]) == app.dimod.sym.Eq
    assert type(output.constraints["Total time"]) == app.dimod.sym.Le

    #  Temporary use of internal method until a non-internal methos is availibele
    if weight_cost_radio_val == "soft":
        output._soft["Total cost"] == app.dimod.constrained.SoftConstraint(weight=weight_cost_val,
            penalty='quadratic')
        output._soft["Total time"] == app.dimod.constrained.SoftConstraint(weight=weight_time_val,
            penalty='quadratic')
