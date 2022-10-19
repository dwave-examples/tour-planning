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

from tour_planning import names_leg_inputs

from app import disable_buttons

job_submit_state = ContextVar('job_submit_state')

parametrize_names = "job_submit_state_val, btn_cancel_style, btn_cancel_disabled, " + \
    ", ".join([key for key in names_leg_inputs])

parametrize_vals = [
("Status: SUBMITTED", dict(), True, True, True, True),
("Status: PENDING", dict(), False, True, True, True),
("Status: IN_PROGRESS", dict(display="none"), True, no_update, no_update, \
    no_update),
("Status: CANCELLED", dict(display="none"),  False, False, False, False),
("Status: FAILED", dict(display="none"),  False, False, False, False),
("Status: COMPLETED", dict(display="none"),  False, False, False, False),
("Status: FAKE", no_update, no_update, no_update, no_update, no_update)]

@pytest.mark.parametrize(parametrize_names,parametrize_vals)
def test_disable_buttons(job_submit_state_val, btn_cancel_style, btn_cancel_disabled,
    num_legs, max_leg_length, min_leg_length):
    """Test disabling buttons used during job submission."""

    def run_callback():
        context_value.set(AttributeDict(**
            {"triggered_inputs": [{"prop_id": "job_submit_state.children"}]}))

        return disable_buttons(job_submit_state.get())

    job_submit_state.set(job_submit_state_val)

    ctx = copy_context()

    output = ctx.run(run_callback)

    assert output == (btn_cancel_style, btn_cancel_disabled,
        num_legs, max_leg_length, min_leg_length)
