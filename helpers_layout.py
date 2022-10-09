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

from dash.dcc import Input, Slider, RadioItems
from dash import html
import numpy as np

from tour_planning import leg_ranges, weight_ranges, budget_ranges
from tour_planning import leg_init_values, weight_init_values, budget_init_values

__all__ = ["_dcc_input", "_dcc_slider", "_dcc_radio"]

ranges = {**leg_ranges, **weight_ranges, **budget_ranges}
init_values = {**leg_init_values, **weight_init_values, **budget_init_values}

def _dcc_input(name, step=None):
    """Construct ``dash.Input`` element for layout."""

    suffix = ""
    if "_slider" in name:
        suffix = "_slider"
        name = name.replace("_slider", "")
    return Input(
        id=f"{name}{suffix}",
        type="number",
        min=ranges[name][0],
        max=ranges[name][1],
        step=step,
        value=init_values[name])

def _dcc_slider(name, step=1, discrete_slider=False):
    """Construct ``dash.Slider`` elements for layout."""

    suffix = ""
    if "_slider" in name:
        suffix = "_slider"
        name = name.replace("_slider", "")
    max_range = ranges[f"{name}"][1]
    init_val = init_values[f"{name}"]
    if not discrete_slider: # log slider
        max_range = np.log10(max_range)
        init_val = np.log10(init_val)
        marks={ranges[f"{name}"][0]:
                {"label": "Soft", "style": {"color": "white"}},
            int(max_range):
                {"label": "Softish", "style": {"color": "white"}}}
    else:
        marks={i: {"label": f"{str(i)}", "style": {"color": "white"}} for i in
        range(ranges[name][0], ranges[name][1] + 1, 2*step)}

    return Slider(
        id=f"{name}{suffix}",
        min=ranges[f"{name}"][0],
        max=max_range,
        marks=marks,
        step=step,
        value=init_val,)

def _dcc_radio(name):
    """Construct ``dash.RadioItem`` elements for layout."""

    return RadioItems([
        {"label": html.Div(['Soft   '], style={'color': 'white', 'font-size': 12}),
        "value": "soft",},
        {"label": html.Div(['   Hard'], style={'color': 'white', 'font-size': 12}),
        "value": "hard",},], value='soft', id=f"{name}_radio",
        inputStyle={"margin-right": "20px"})
