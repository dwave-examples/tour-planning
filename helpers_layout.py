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

from dash.dcc import Input, Link, Slider, RadioItems
import dash_bootstrap_components as dbc
from dash import html

from tour_planning import (locomotion_ranges, leg_ranges, slope_ranges,
    weight_ranges, budget_ranges)
from tour_planning import (locomotion_init_values, leg_init_values, slope_init_values,
    weight_init_values, budget_init_values)

__all__ = ["_dcc_input", "_dcc_slider", "_dcc_radio", "_dbc_modal"]

ranges = {**locomotion_ranges, **leg_ranges, **slope_ranges, **weight_ranges,
    **budget_ranges}
init_values = {**locomotion_init_values, **leg_init_values, **slope_init_values,
    **weight_init_values, **budget_init_values}

def _dcc_input(name, step=None):
    """Construct ``dash.Input`` element for layout."""

    return Input(
        id=name,
        type="number",
        min=ranges[name][0],
        max=ranges[name][1],
        step=step,
        value=init_values[name])

def _dcc_slider(name, step=1):
    """Construct ``dash.Slider`` elements for layout."""

    return Slider(
        id=f"{name}",
        min=ranges[f"{name}"][0],
        max=ranges[f"{name}"][1],
        marks={i: {"label": f"{str(i)}", "style": {"color": "white"}} for i in
            range(ranges[name][0], ranges[name][1] + 1, 2*step)},
        step=step,
        value=init_values[f"{name}"],)

labels = {"hardsoft": ["Soft", "Hard"],
          "penalty": ["Linear", "Quadratic"],
          "active": ["On", "Off"]}

def _dcc_radio(name, suffix):
    """Construct ``dash.RadioItem`` elements for layout."""

    margin = {"hardsoft": {"margin-right": "20px"},
              "penalty": {"margin-right": "30px"},
              "active": {"margin-right": "20px"}}

    return RadioItems([
        {"label": html.Div([labels[suffix][0]], style={'color': 'white', 'font-size': 12}),
        "value": labels[suffix][0].lower(),},
        {"label": html.Div([labels[suffix][1]], style={'color': 'white', 'font-size': 12}),
        "value": labels[suffix][1].lower(),},], value=labels[suffix][0].lower(),
        id=f"{name}_{suffix}", inputStyle=margin[suffix])

modal_texts = {"solver": ["Leap Hybrid CQM Solver Inaccessible",
    [
        html.Div([
        html.Div("Could not connect to a Leap hybrid CQM solver."),
        html.Div(["""
    If you are running locally, set environment variables or a
    dwave-cloud-client configuration file as described in the
    """,
        Link(children=[html.Div(" Ocean")],
            href="https://docs.ocean.dwavesys.com/en/stable/overview/sapi.html",
            style={"display":"inline-block"}),
        "documentation."],
            style={"display":"inline-block"}),
        html.Div(["If you are running in the Leap IDE, see the ",
        Link(children=[html.Div("Leap IDE dumentation")],
            href="https://docs.dwavesys.com/docs/latest/doc_ide_user.html",
            style={"display":"inline-block"}),
        "documentation"],
            style={"display":"inline-block"}),])]
    ],
    "usemodes": ["One Locomotion Mode is Required",
    [html.Div("You must set at least one mode of locomotion to 'Use'.")]]}

def _dbc_modal(name):
    name = name.split("_")[1]
    return [html.Div([
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle(modal_texts[name][0])),
            dbc.ModalBody(modal_texts[name][1]),],
                id=f"{name}_modal", size="sm")])]
