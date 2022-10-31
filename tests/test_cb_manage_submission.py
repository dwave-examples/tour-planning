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

import datetime

from helpers.formatting import tour_from_json
from helpers.jobs import elapsed

from app import names_leg_inputs, names_budget_inputs, names_weight_inputs

from app import manage_submission

n_clicks = ContextVar('n_clicks')
n_intervals = ContextVar('n_intervals')
job_id = ContextVar('job_id')
job_submit_state = ContextVar('job_submit_state')
job_submit_time = ContextVar('job_submit_time')

def mock_get_status(client, job_id, job_submit_time):

    if job_id == "first few attempts":
        return None
    if job_id == "first returned status":
        return "PENDING"
    if job_id == "early returning statuses":
        return "PENDING"
    if job_id == "impossible input status":
        return "should make no difference"
    if job_id == "1":
        return "IN_PROGRESS"
    if job_id == "2":
        return "COMPLETED"
    if job_id == "3":
        return "CANCELLED"
    if job_id == "4":
        return "FAILED"

parametrize_names = "btn_solve_cqm_clicks, wd_job_intervals, job_id_val, submit_state_in, " +\
" submit_time_in, btn_solve_cqm_disabled, wd_job_disabled, wd_job_interval, " + \
"wd_job_n, submit_state_out, submit_time_out, job_elapsed_time_val"

before_test = datetime.datetime.now().strftime("%c")
parametrize_vals = [
(1, 0, "123", "Status: READY", before_test, True, False, 0.2*1000, 0,
    "Status: SUBMITTED", 0.5, 0.5),
(1, 0, "123", "Status: CANCELLED", before_test, True, False, 0.2*1000, 0,
    "Status: SUBMITTED", 0.5, 0.5)]

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

    assert output[0:5] == (btn_solve_cqm_disabled, wd_job_disabled, wd_job_interval,
        wd_job_n, submit_state_out)
    assert elapsed(output[5]) <= submit_time_out
    assert int(output[6].split(" ")[1]) <= job_elapsed_time_val

before_test = datetime.datetime.now().strftime("%c")
parametrize_vals = [
    (1, 0, "first few attempts", "Status: SUBMITTED", before_test, True, False,
        0.2*1000, 0, "Status: SUBMITTED", no_update, 15),
    (1, 0, "first few attempts", "Status: PENDING", before_test, True, False,
        0.2*1000, 0, "Status: SUBMITTED", no_update, 15),
    (1, 0, "first returned status", "Status: SUBMITTED", before_test, True, False,
        1*1000, 0, "Status: PENDING", no_update, 15),
    (1, 0, "first returned status", "Status: PENDING", before_test, True, False,
        1*1000, 0, "Status: PENDING", no_update, 15),
    (1, 0, "early returning statuses", "Status: PENDING", before_test, True, False,
        1*1000, 0, "Status: PENDING", no_update, 15),
    (1, 0, "1", "Status: PENDING", before_test, True, False,
        1*1000, 0, "Status: IN_PROGRESS", no_update, 15),
    (1, 0, "2", "Status: PENDING", before_test, True, False,
        1*1000, 0, "Status: COMPLETED", no_update, 15),
    (1, 0, "2", "Status: IN_PROGRESS", before_test, True, False,
        1*1000, 0, "Status: COMPLETED", no_update, 15),
    (1, 0, "3", "Status: PENDING", before_test, True, False,
        1*1000, 0, "Status: CANCELLED", no_update, 15),
    (1, 0, "3", "Status: IN_PROGRESS", before_test, True, False,
        1*1000, 0, "Status: CANCELLED", no_update, 15),
    (1, 0, "4", "Status: PENDING", before_test, True, False,
        1*1000, 0, "Status: FAILED", no_update, 15),
    (1, 0, "4", "Status: IN_PROGRESS", before_test, True, False,
        1*1000, 0, "Status: FAILED", no_update, 15),
    (1, 0, "status not checked", "Status: COMPLETED", before_test, False,
        True, 0.1*1000, 0, no_update, no_update, 15),
    (1, 0, "status not checked", "Status: CANCELLED", before_test, False,
        True, 0.1*1000, 0, no_update, no_update, 15),
    (1, 0, "status not checked", "Status: FAILED", before_test, False,
        True, 0.1*1000, 0, no_update, no_update, 15),
    (1, 0, "impossible input status", "Status: READY", before_test, False, True,
        0, 0, "Status: ERROR", no_update, "Please restart"),]

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
@patch("app.jobs.get_status", mock_get_status)
def test_manage_submission_watchdog(btn_solve_cqm_clicks, wd_job_intervals,
    job_id_val, submit_state_in, submit_time_in, btn_solve_cqm_disabled,
    wd_job_disabled, wd_job_interval, wd_job_n, submit_state_out, submit_time_out,
    job_elapsed_time_val):
    """Test returns from watchdog trigger."""

    def run_callback():
        context_value.set(AttributeDict(
            **{"triggered_inputs": [{"prop_id": "wd_job.n_intervals"}]}))

        return manage_submission(n_clicks.get(), n_intervals.get(), \
            job_id.get(), job_submit_state.get(), job_submit_time.get())

    n_clicks.set(btn_solve_cqm_clicks)
    n_intervals.set(wd_job_intervals)
    job_id.set(job_id_val)
    job_submit_state.set(submit_state_in)
    job_submit_time.set(submit_time_in)

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[0:6] == (btn_solve_cqm_disabled, wd_job_disabled, wd_job_interval,
        wd_job_n, submit_state_out, submit_time_out)

    if job_id_val == "impossible input status":
        assert output[6] == job_elapsed_time_val
    else:
        assert int(output[6].split(" ")[1]) <= job_elapsed_time_val
