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

import time

from dwave.cloud import api

from app import cancel_submission

btn_cancel = ContextVar('btn_cancel')
job_id = ContextVar('job_id')

status = api.models.ProblemStatus(id='1',  type=api.constants.ProblemType.CQM,
    solver="Henry", submitted_on=time.time(), status=api.constants.ProblemStatus.CANCELLED)

def mock_cancel(client, job_id):

    err = "Problem does not exist or apitoken does not have access"

    if job_id == "123":
        return status
    if job_id == "456":
        raise api.exceptions.ResourceNotFoundError(err)

@pytest.mark.parametrize("btn_cancel_val, job_id_val, alert_cancel_text_val, " + \
    "alert_cancel_state_val",
    [(1, "123", "Cancelled job 123", True),
     (1, "456", "Could not cancel job: Problem does not exist or apitoken does not have access", True),
     (0, "123", "Cancelled job 123", True),])
@patch("app.jobs.cancel", mock_cancel)
def test_cancel_submission(btn_cancel_val, job_id_val, alert_cancel_text_val,
    alert_cancel_state_val):
    """Test job cancellation."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "btn_cancel.n_clicks"}],
             "state_values": [{"prop_id": "job_id.children"}]}))

        return cancel_submission(btn_cancel.get(), job_id.get())

    btn_cancel.set(btn_cancel_val)
    job_id.set(job_id_val)

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output[0] == alert_cancel_text_val
    assert output[1] == alert_cancel_state_val
