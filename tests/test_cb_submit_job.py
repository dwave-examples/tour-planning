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

import dimod

from helpers.formatting import state_to_json, state_from_json

from app import names_budget_inputs

from app import submit_job

problem_print_placeholder = '[{"length": 9.4, "uphill": 0.1, "toll": false}, {"length": 6.9, "uphill": 2.5, "toll": false}]'

job_submit_time = ContextVar("job_submit_time")
problem_print_code = ContextVar("problem_print_code")
max_leg_slope = ContextVar("max_leg_slope")
for key in names_budget_inputs:
    vars()[key] = ContextVar(f"{key}")
weights_state = ContextVar("weights_state")
locomotion_state = ContextVar("locomotion_state")
max_runtime = ContextVar("max_runtime")

state_vals = [{"prop_id": "problem_print_code"}]
state_vals.extend([{"prop_id": "max_leg_slope"}])
state_vals.extend([{"prop_id": f"{key}.value"} for key in
    names_budget_inputs])
state_vals.extend([{"prop_id": "weights_state.children"}])
state_vals.extend([{"prop_id": "locomotion_state"}])

class fake_computation():

    def __init__(self):
        self.cqm = " "
        self.return_cqm = False

    def result(self):
        return "12345"

    def wait_id(self):
        if not self.return_cqm:
            return "67890"
        else:
            return self.cqm

class fake_solver():

    def __init__(self):
        self.a_fake_computation = fake_computation()

    def upload_cqm(self, cqm):
        self.a_fake_computation.cqm = cqm
        return self.a_fake_computation

    def sample_cqm(self, id, label, time_limit):
        if time_limit == "return cqm":
            self.a_fake_computation.return_cqm = True
        return self.a_fake_computation

class mock_client():

    @classmethod
    def get_solver(cls, **kwargs):
        a_fake_solver = fake_solver()
        return a_fake_solver
#
weights_json = state_to_json({"weight_cost":  {"weight": None, "penalty": "linear"},
     "weight_time": {"weight": None, "penalty": "linear"},
     "weight_slope": {"weight": 55, "penalty": "quadratic"}})

parametrize_names = "job_submit_time_val, problem_print_code_val, max_leg_slope_val, " + \
    ", ".join([f'{key}_val ' for key in names_budget_inputs]) + \
    ", weights_val, max_runtime_val, job_id"

parametrize_vals = [
    ("high tea time", problem_print_placeholder, 8, 100, 20, weights_json,
        5, "67890"),
    ("later", problem_print_placeholder, 8, 100, 20, weights_json,
        20, "67890"),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.client", mock_client)
def test_submit_job(locomotion_data_default, job_submit_time_val, problem_print_code_val,
    max_leg_slope_val,  max_cost_val, max_time_val, weights_val, max_runtime_val, job_id):
    """Test job submission."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "job_submit_time.children"}],
            "state_values": state_vals}))

        return submit_job(job_submit_time.get(), problem_print_code.get(), \
            max_leg_slope.get(), max_cost.get(), max_time.get(), \
            weights_state.get(),locomotion_state.get(), max_runtime.get())

    job_submit_time.set(vars()["job_submit_time_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs:
        globals()[key].set(vars()[key + "_val"])
    weights_state.set(weights_val)
    locomotion_state.set(state_to_json(locomotion_data_default))
    max_runtime.set(vars()["max_runtime_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output == job_id


parametrize_constants = ["high tea time", problem_print_placeholder, 8, 100, 20]
parametrize_vals = []
hardsoft = [h for h in product(["soft", "hard"], repeat=3)]
penalty = [p for p in product(["linear", "quadratic"], repeat=3)]
for h, p in zip(hardsoft, penalty):
    weights_json = state_to_json({
        "weight_cost":  {
            "weight": None if h[0] == "hard" else 33,
            "penalty": p[0]},
         "weight_time": {
            "weight": None if h[1] == "hard" else 44,
            "penalty": p[1]},
         "weight_slope": {
                "weight": None if h[2] == "hard" else 55,
                "penalty": p[2]}})
    parametrize_vals.append(tuple([*parametrize_constants, weights_json,
        "return cqm", "not used"]))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.client", mock_client)
def test_submit_job_weights(locomotion_data_default, job_submit_time_val,
    problem_print_code_val, max_leg_slope_val, max_cost_val, max_time_val,
    weights_val, max_runtime_val, job_id):
    """Test job submission incorporates penalties correctly.."""

    def run_callback():
        context_value.set(AttributeDict(
            **{
            "triggered_inputs": [{"prop_id": "job_submit_time.children"}],
            "state_values": state_vals}))

        return submit_job(job_submit_time.get(), problem_print_code.get(), \
            max_leg_slope.get(), max_cost.get(), max_time.get(), \
            weights_state.get(), locomotion_state.get(), max_runtime.get())

    job_submit_time.set(vars()["job_submit_time_val"])
    problem_print_code.set(vars()["problem_print_code_val"])
    max_leg_slope.set(vars()["max_leg_slope_val"])
    for key in names_budget_inputs:
        globals()[key].set(vars()[key + "_val"])
    weights_state.set(weights_val)
    locomotion_state.set(state_to_json(locomotion_data_default))
    max_runtime.set(vars()["max_runtime_val"])

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert type(output) == dimod.constrained.ConstrainedQuadraticModel

    weight_vals = state_from_json(weights_val)

    if weight_vals["weight_cost"]["weight"] != None:
        assert output._soft["Total cost"] == dimod.constrained.SoftConstraint(
            weight=weight_vals["weight_cost"]["weight"],
            penalty=weight_vals["weight_cost"]["penalty"])
    else:
        with pytest.raises(Exception):
            output.constraint["Total cost"] == dimod.constrained.SoftConstraint(
                weight=weight_vals["weight_cost"]["weight"],
                penalty=weight_vals["weight_cost"]["penalty"])
