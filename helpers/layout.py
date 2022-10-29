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

__all__ = ["_dcc_input", "_dcc_slider", "_dcc_radio", "_dbc_modal",
    "description_feasibility_plot", "description_space_plot", "description_time_plot",
    "description_problem_print", "description_solutions_print", "description_cqm_print",
    "description_locomotion_print"]

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
        value=init_values[name],
        style={"max-width": "95%"})

def _dcc_slider(name, step=1):
    """Construct ``dash.Slider`` elements for layout."""

    return Slider(
        id=f"{name}",
        min=ranges[f"{name}"][0],
        max=ranges[f"{name}"][1],
        marks={i: {"label": f"{str(i)}", "style": {"color": "white"}} for i in
            range(ranges[name][0], ranges[name][1] + 1, 2*step)},
        step=step,
        value=init_values[f"{name}"])

labels = {"hardsoft": ["Soft", "Hard"],
          "penalty": ["Linear", "Quadratic"],
          "active": ["On", "Off"]}

def _dcc_radio(name, suffix):
    """Construct ``dash.RadioItem`` elements for layout."""

    return RadioItems([
        {"label": html.Div([labels[suffix][0]]), "value": labels[suffix][0].lower(),},
        {"label": html.Div([labels[suffix][1]]), "value": labels[suffix][1].lower(),},],
        value=labels[suffix][0].lower(),
        id=f"{name}_{suffix}",
        inputStyle={"margin-right": "10px", "margin-bottom": "10px"},
        labelStyle={"color": "white", "font-size": 12, "display": "flex"})

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



description_space_plot = ["""The tour in space represented as a colored bar,
with each segment being a leg, its relative width the length of the leg, and its
color the elevation gain for that leg. Toll booths, if present, are shown as icons
above the tour (there is a constraint not to drive on legs with toll booths).
For submitted jobs, the modes of locomotion in the best returned solution are
written onto the tour and shown as icons below it."""]

description_time_plot = ["""A time graph for the best feasible solution
returned from your job submission.""",
html.Br(),
"""The colored bar represents the tour in time, with each segment being a leg,
its relative width and color the time and cost, respectively, of traversing the
leg at the speed of the mode of locomotion selected by the best returned solution.
Toll booths, if present, are shown as icons above the tour (there is a constraint
not to drive on legs with toll booths). The best modes of locomotion found in returned
solutions are written onto the tour and shown as icons below it.""",
html.Br(),
"""Look here to see the overall duration of the tour."""]

description_feasibility_plot = ["""All returned solutions for a job submission
(not just the best solution).""",
html.Br(),
"""Feasible solutions are plotted in blue and infeasible solutions in red.
Data-point size is proportional to the number of occurrences of a solution.""",
html.Br(),
"""Look here to see the quality of your solutions (e.g., overall tour cost and
exercise).""",
html.Br(),
"""You can hover over a data point to see information about it and can rotate and
zoom in on parts of this graphic."""]

description_problem_print = """Information on the legs configured
for the tour (length, slope, and toll booths), formatted for both reading and
copying and pasting into your code."""

description_solutions_print = """The best solution found, formatted for reading,
and the returned dimod sampleset, which you can copy and paste into your
code or Python terminal."""

description_cqm_print = ["""The constrained quadratic model (CQM)
generated for your configured tour and its constraints.""",
html.Br(),
"""To understand how the CQM is built up, it can be helpful to look at this display
for a minimal tour (set the number of legs to one, the maximum leg length to one,
enable a single mode of locomotion, turn off tollbooths, etc), and then gradually
increment the complexity while studying the changes to the resultant CQM."""]

description_locomotion_print = ["""Information about your configured tour,
such as the minimum, maximum, and average values of cost and time, and the
available modes of locomotion.""",
html.Br(),
"""Here you can also configure parameters for the modes of locomotion used in the
problem.""",
html.Br(),
"""Look here to see what values make sense for your tour budgets (cost and duration)."""]
