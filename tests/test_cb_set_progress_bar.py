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

from helpers.jobs import job_bar, TERMINATED, RUNNING

from app import set_progress_bar

job_submit_state = ContextVar('job_submit_state')

parametrize_vals = [
(f"Status: {status}", job_bar[status][0], job_bar[status][1]) for status in TERMINATED + RUNNING]
parametrize_vals.extend([tuple(["Status: READY", job_bar["READY"][0], job_bar["READY"][1]])])
parametrize_vals.extend([tuple(["Status: BREAK FUNCTION", "exception", "exception"])])

@pytest.mark.parametrize("job_submit_state_val, bar_job_status_value, bar_job_status_color",
parametrize_vals)
def test_set_progress_bar(job_submit_state_val, bar_job_status_value, bar_job_status_color):
    """Test job-submission progress bar."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "job_submit_state.children"}]}))

        return set_progress_bar(job_submit_state.get())

    job_submit_state.set(job_submit_state_val)

    ctx = copy_context()

    try:
        output = ctx.run(run_callback)
        assert output == (bar_job_status_value, bar_job_status_color)
    except KeyError:
        assert job_submit_state_val == "Status: BREAK FUNCTION"
