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

in_print_generate_legs = """
Configurable inputs have these supported ranges and current values:
               Min.    Max. Current Value Last Updated Input
num_legs          5     100            10
max_leg_length    1      20            10 <<--
min_leg_length    1      20             2
...
weight_slope      0  100000           150
"""

in_print_no_update = """
Configurable inputs have these supported ranges and current values:
               Min.    Max. Current Value Last Updated Input
num_legs          5     100            10
...
max_time          0  100000            13
weight_cost       0  100000           100 <<--
...
"""

in_print_no_last_change = """
Configurable inputs have these supported ranges and current values:
               Min.    Max. Current Value Last Updated Input
num_legs          5     100            10
...
max_time          0  100000            13
weight_cost       0  100000           100
...
"""

output_placeholder = " "

import app

input_print = ContextVar("input_print")
for key in app.leg_inputs.keys():
    vars()[key] = ContextVar(f"{key}")

@pytest.mark.parametrize("input_print_val, " +
    ",".join([f'{key}_val' for key in app.leg_inputs.keys()]) +
    ", problem_print_code_val, problem_print_human_val",
    [(in_print_no_update, 10, 10, 3, 8, no_update, no_update),
    (in_print_generate_legs, 10, 10, 3, 8, output_placeholder, output_placeholder),
    (in_print_no_last_change, 10, 10, 3, 8, output_placeholder, output_placeholder)])
def test_legs(mocker, input_print_val, num_legs_val,
    max_leg_length_val, min_leg_length_val, max_leg_slope_val,
    problem_print_code_val, problem_print_human_val):

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "input_print.value"}],
            "state_values": [{"prop_id": f"{key}.value"} for key in app.leg_inputs.keys()]}))

        return app.legs(input_print.get(), num_legs.get(), max_leg_length.get(),\
            min_leg_length.get(), max_leg_slope.get())

    input_print.set(vars()["input_print_val"])
    for key in app.leg_inputs.keys():
        globals()[key].set(vars()[f"{key}_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    if input_print_val == in_print_no_update:
        assert output == (no_update, no_update)

    if input_print_val in [in_print_generate_legs, in_print_no_last_change]:
        output_code = tour_from_json(output[0])
        assert set(output_code[0]) - \
                set({"length": 2.6, "uphill": 7.1, "toll": True}) == set()
        assert "length" in output[1].partition('\n')[0]
