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

from dash.dcc import Input, Slider

from tour_planning import init_cqm, init_tour

__all__ = ["_dcc_input", "_dcc_slider",]

def _dcc_input(name, config_vals, step=None):
    """Construct ``dash.Input`` element for layout."""
    suffix = ""
    if "_slider" in name:
        suffix = "_slider"
        name = name.replace("_slider", "")
    return Input(
        id=f"{name}{suffix}",
        type="number",
        min=config_vals[name][0],
        max=config_vals[name][1],
        step=step,
        value=config_vals[name][2])

def _dcc_slider(name, config_vals, step=1, discrete_slider=False):
    """Construct ``dash.Slider`` elements for layout."""
    suffix = ""
    if "_slider" in name:
        suffix = "_slider"
        name = name.replace("_slider", "")
    if not discrete_slider:
        marks={config_vals[f"{name}"][0]:
            {"label": "Soft", "style": {"color": "white"}},
            config_vals[f"{name}"][1]:
            {"label": "Hard", "style": {"color": "white"}}}
    else:
        marks={i: {"label": f"{str(i)}", "style": {"color": "white"}} for i in
        range(config_vals[name][0], init_tour[name][1] + 1, 2*step)}

    return Slider(
        id=f"{name}{suffix}",
        min=config_vals[f"{name}"][0],
        max=config_vals[f"{name}"][1],
        marks=marks,
        step=step,
        value=config_vals[f"{name}"][2],)
