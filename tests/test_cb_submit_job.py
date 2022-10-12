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
from itertools import product

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

from formatting import tour_from_json

from app import names_budget_inputs, names_weight_inputs
from app import submit_job

problem_print_placeholder = '[{"length": 9.4, "uphill": 0.1, "toll": false}, {"length": 6.9, "uphill": 2.5, "toll": false}]'

job_submit_time = ContextVar("job_submit_time")
problem_print_code = ContextVar("problem_print_code")
max_leg_slope = ContextVar("max_leg_slope")
for key in names_budget_inputs + names_weight_inputs:
    vars()[key] = ContextVar(f"{key}")
for key in names_weight_inputs:
    vars()[f"{key}_hardsoft"] = ContextVar(f"{key}_hardsoft")
for key in names_weight_inputs:
    vars()[f"{key}_penalty"] = ContextVar(f"{key}_penalty")
max_runtime = ContextVar("max_runtime")


state_vals = [{"prop_id": "problem_print_code"}]
state_vals.extend([{"prop_id": "max_leg_slope"}])
state_vals.extend([{"prop_id": f"{key}.value"} for key in
    names_budget_inputs + names_weight_inputs])
state_vals.extend([{"prop_id": f"{key}_hardsoft.value"} for key in names_weight_inputs])
state_vals.extend([{"prop_id": f"{key}_penalty.value"} for key in names_weight_inputs])

class fake_computation():

    def __init__(self):
        pass

    def result(self):
        return "12345"

    def wait_id(self):
        return "67890"

class fake_solver():

    def __init__(self):
        self.a_fake_computation = fake_computation()

    def upload_cqm(self, cqm):
        return self.a_fake_computation

    def sample_cqm(self, id, label, time_limit):
        return self.a_fake_computation

def mock_get_solver(**kwargs):
    a_fake_solver = fake_solver()
    return a_fake_solver

parametrize_names = "job_submit_time_val, problem_print_code_val, max_leg_slope_val, " + \
    ", ".join([f'{key}_val ' for key in names_budget_inputs + names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_hardsoft_val ' for key in names_weight_inputs]) + \
    ", " + ", ".join([f'{key}_penalty_val ' for key in names_weight_inputs]) + \
    ", max_runtime_val, job_id"

parametrize_vals = [
    ("high tea time", problem_print_placeholder, 8, 100, 20, 33, 44, 55, "soft",
        "soft", "soft", "linear", "linear", "linear", 5, "67890"),
    ("later", problem_print_placeholder, 8, 100, 20, 33, 44, 55, "soft",
        "soft", "soft", "linear", "linear", "linear", 20, "67890"),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.client.get_solver", mock_get_solver)
def test_submit_job(job_submit_time_val, problem_print_code_val, max_leg_slope_val,
    max_cost_val, max_time_val, weight_cost_val, weight_time_val, weight_slope_val,
    weight_cost_hardsoft_val, weight_time_hardsoft_val, weight_slope_hardsoft_val,
    weight_cost_penalty_val, weight_time_penalty_val, weight_slope_penalty_val,
    max_runtime_val, job_id):
    """Test job submission."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "job_submit_time.children"}],
            "state_values": state_vals}))

        return submit_job(job_submit_time.get(), problem_print_code.get(), max_leg_slope.get(),\
            max_cost.get(), max_time.get(), weight_cost.get(), weight_time.get(), \
            weight_slope.get(), weight_cost_hardsoft.get(), weight_time_hardsoft.get(), \
            weight_slope_hardsoft.get(), weight_cost_penalty.get(), \
            weight_time_penalty.get(), weight_slope_penalty.get(), max_runtime.get())

    job_submit_time.set(vars()["job_submit_time_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs + names_weight_inputs:
        globals()[key].set(vars()[key + "_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_hardsoft"].set(vars()[f"{key}_hardsoft_val"])
    for key in names_weight_inputs:
        globals()[f"{key}_penalty"].set(vars()[f"{key}_penalty_val"])
    max_runtime.set(vars()["max_runtime_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output == job_id
