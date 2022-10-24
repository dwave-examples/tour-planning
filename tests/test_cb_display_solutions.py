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

from contextvars import copy_context, ContextVar
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import no_update

import json

import dimod
from dwave.cloud import api

from helpers.jobs import TERMINATED

from app import display_solutions

job_submit_state = ContextVar('job_submit_state')
job_id = ContextVar('job_id')

sampleset = dimod.SampleSet.from_samples([
    {"bus_0": 0, "drive_0": 1, "cycle_0": 0, "walk_0": 0},
    {"bus_0": 0, "drive_0": 0, "cycle_0": 0, "walk_0": 1}], "BINARY", [0, 0])
sampleset = dimod.append_data_vectors(sampleset, is_satisfied=[[True], [True]])
sampleset_feasible = dimod.append_data_vectors(sampleset, is_feasible=[[True],[False]])
sampleset_infeasible = dimod.append_data_vectors(sampleset, is_feasible=[[False],[False]])

class fake_future():

    def __init__(self, feasible):

        if feasible:
            self.sampleset = sampleset_feasible
        else:
            self.sampleset = sampleset_infeasible

class mock_client():

    @classmethod
    def retrieve_answer(cls, job_id):
        if job_id == "123":
            a_fake_future = fake_future(True)
            return a_fake_future
        else:
            a_fake_future = fake_future(False)
            return a_fake_future

parametrize_vals = [
("Status: COMPLETED", "123", sampleset_feasible, "Feasible solutions: 50.0%"),
("Status: CANCELLED", "123", "No solutions for last submission", "No solutions for last submission"),
("Status: PENDING", "123", no_update, no_update),
("Status: COMPLETED", "456", json.dumps(sampleset_infeasible.to_serializable()),
    "No feasible solutions found."),]

@pytest.mark.parametrize("job_submit_state_val, job_id_val, solutions_code, solutions_human",
    parametrize_vals)
@patch("app.client", mock_client)
def test_display_solutions(job_submit_state_val, job_id_val, solutions_code,
    solutions_human):
    """Test display of returned samplesets."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "job_submit_state.children"}],
             "state_values": [{"prop_id": "job_id.children"}]}))

        return display_solutions(job_submit_state.get(), job_id.get())

    job_submit_state.set(job_submit_state_val)
    job_id.set(job_id_val)

    ctx = copy_context()

    output = ctx.run(run_callback)

    if job_submit_state_val == "Status: COMPLETED" and job_id_val == "123":

        assert solutions_code == dimod.SampleSet.from_serializable(json.loads(output[0]))
        assert solutions_human in output[1].split("/n")[0]

    else:

        assert output == (solutions_code, solutions_human)
