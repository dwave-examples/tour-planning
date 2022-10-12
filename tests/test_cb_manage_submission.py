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

from app import names_leg_inputs, names_budget_inputs, names_weight_inputs
from app import manage_submission

n_clicks = ContextVar('n_clicks')
n_intervals = ContextVar('n_intervals')
job_id = ContextVar('job_id')
job_submit_state = ContextVar('job_submit_state')
job_submit_time = ContextVar('job_submit_time')

parametrize_names = "btn_solve_cqm_clicks, wd_job_intervals, job_id_val, submit_state_in, " +\
" submit_time_in, btn_solve_cqm_disabled, wd_job_disabled, wd_job_interval, " + \
"wd_job_n, submit_state_out, submit_time_out, job_elapsed_time_val"
parametrize_vals = [(1, 0, "123", "READY", "now", True, True, 0.2*1000, 0,
    "Status: SUBMITTED", "later", "a few seconds")]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_manage_submission_button_press(btn_solve_cqm_clicks, wd_job_intervals,
    job_id_val, submit_state_in, submit_time_in, btn_solve_cqm_disabled,
    wd_job_disabled, wd_job_interval, wd_job_n, submit_state_out, submit_time_out,
    job_elapsed_time_val):
    """Test pressing SOLVE CQM initiates submission."""

    def run_callback():
        context_value.set(AttributeDict(
            **{"triggered_inputs": [{"prop_id": "btn_solve_cqm.n_clicks"}]}))

        return manage_submission(n_clicks.get(), n_intervals.get(), \
            job_id.get(), job_submit_state.get(), job_submit_time.get())

    n_clicks.set(btn_solve_cqm_clicks)
    n_intervals.set(wd_job_intervals)
    job_id.set(job_id_val)
    job_submit_state.set(submit_state_in)
    job_submit_time.set(submit_time_in)

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[0] == btn_solve_cqm_disabled
