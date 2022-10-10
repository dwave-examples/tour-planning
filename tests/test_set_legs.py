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

import random

from app import names_leg_inputs
from tour_planning import leg_ranges, set_legs

parametrize_names = "num_legs_val, max_leg_length_val, min_leg_length_val, " + \
    "max_leg_slope_val"

parametrize_vals = []
for i in range(5):
    leg_vals = [random.randint(leg_ranges[key][0], leg_ranges[key][1]) for key
        in names_leg_inputs]
    parametrize_vals.append(tuple(leg_vals))

@pytest.mark.parametrize(parametrize_names, parametrize_vals)
def test_set_legs(num_legs_val, max_leg_length_val,
    min_leg_length_val, max_leg_slope_val):
    """Test that legs are correctly generated."""

    output = set_legs(num_legs_val, max_leg_length_val, min_leg_length_val,
        max_leg_slope_val)

    assert set(output[0].keys()) - set(["length", "uphill", "toll"]) == set()