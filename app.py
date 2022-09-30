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

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import json
import plotly.express as px
import pandas as pd
import random
import numpy as np
from pprint import pprint
import time, datetime

from helpers import *
from formatting import *
from tour_planning import init_cqm, init_tour, init_legs
from tour_planning import build_cqm, set_legs, transport
from tool_tips import tool_tips

import dimod
from dwave.cloud.hybrid import Client
from dwave.cloud.api import Problems

modes = transport.keys()  # global, but not user modified
num_modes = len(modes)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

try:
    client = Client.from_config(profile="test")
except Exception as client_err:
    client = None

# Helper functions
##################

def _dcc_input(name, config_vals, step=None, with_slider=""):
    """Sets input to dash.Input elements in layout."""
    name = f"{name}{with_slider}"
    return dcc.Input(
        id=name,
        type="number",
        min=config_vals[name][0],
        max=config_vals[name][1],
        step=step,
        value=config_vals[name][2])

def _dcc_slider(name, config_vals, step=1, with_suffix=False, discrete_slider=False):
    """Sets input to dash.Input elements in layout."""
    suffix_slider = suffix_input = ""
    if with_suffix:
        suffix_slider = "_slider"
        suffix_input = "_input"
    if not discrete_slider:
        marks={config_vals[f"{name}{suffix_input}"][0]:
                {"label": "Soft", "style": {"color": 'white'}},
            config_vals[f"{name}{suffix_input}"][1]:
                {"label": "Hard", "style": {"color": 'white'}}}
    else:
        marks={i: {"label": f'{str(i)}', "style": {"color": "white"}} for i in
        range(config_vals[name][0], init_tour[name][1] + 1, 2*step)}

    return dcc.Slider(
        id=f"{name}{suffix_slider}",
        min=config_vals[f"{name}{suffix_input}"][0],
        max=config_vals[f"{name}{suffix_input}"][1],
        marks=marks,
        step=step,
        value=config_vals[f"{name}{suffix_input}"][2],)

# Problem-submission section
############################

solver_card = dbc.Card([
    html.H4("Job Submission", className="card-title"),
    dbc.Col([
        dbc.Button("Solve CQM", id="btn_solve_cqm", color="primary", className="me-1"),
        dcc.Interval(id="wd_job", interval=None, n_intervals=0, disabled=True, max_intervals=1),
        dbc.Progress(id="bar_job_status", value=0, color="info", className="mb-3"),
        html.P(id="job_submit_state", children=out_job_submit_state("READY")),   # if no client change ready
        html.P(id="job_submit_time", children="", style = dict(display="none")),
        html.P(id="job_id", children="", style = dict(display="none")),
        html.P(id="job_elapsed_time", children=""),
        dbc.Button("Cancel Job", id="btn_cancel", color="warning", className="me-1",
            style = dict(display="none")),]),],
    color="secondary")

# Tab-construction section
##########################
tabs = {}

graphs = {
    "Space": "Displays your configured tour, with leg distance as " + \
        "relative length and elevation by color. Will display best found mode of transport.",
    "Time": "Will display best found solution, with leg duration as relative length.",
    "Diversity": "Will display all returned solutions to submitted problems."}
tabs["Graph"] = dbc.Tabs([
    dbc.Tab(dbc.Card([
        dbc.Row([
            dbc.Col([
                html.P(id=f"{key}_intro", children=val, style={"color": "black"}),
                dcc.Graph(id=f"{key.lower()}_graph")], width=12) ])]), label=f"{key}",
                    tab_id=f"graph_{key.lower()}",
                    label_style={"color": "white", "backgroundColor": "black"},)
    for key, val in graphs.items()])

viewers = {
    "Problem": "Displays the configured tour: length of each leg, elevation, and "\
        "toll positions.",
    "Solutions": "Displays returned solutions to submitted problems."}
readers = ["Human", "Code"]
viewer_tabs = {}
for key, val in viewers.items():
    tabs[key] = dbc.Tabs([
        dbc.Tab(dbc.Card([
                    dbc.Row([
                        dbc.Col([
                            dcc.Textarea(id=f"{key.lower()}_print_{reader.lower()}", value=val,
                                style={"width": "100%"}, rows=20)])]),]), label=f"{reader} Readable",
                                    tab_id=f"tab_{key}_print_{reader.lower()}",
                                    label_style={"color": "white", "backgroundColor": "black"},)
    for reader in readers])

viewers = {"CQM": "", "Input": "", "Transport": out_transport_human(transport)}
for key, val in viewers.items():
    tabs[key] = dbc.Card([
        dbc.Row([
            dbc.Col([
                dcc.Textarea(id=f"{key.lower()}_print", value=val,
                    style={"width": "100%"}, rows=20)])]),])

# Configuration sections
########################

constraints = {f"weight_{constraint.lower()}": f"{constraint}" for
    constraint in ["Cost", "Time", "Slope"]}

# constraints = [[f"{constraint}", f"weight_{constraint.lower()}"] for constraint
#     in ["Cost", "Time", "Slope"]]
constraint_card = [html.H4("CQM Settings", className="card-title")]
constraint_card.extend([
    html.Div([
        dbc.Label(f"{val} Weight"),
        html.Div([
            _dcc_input(key, init_cqm, step=1, with_slider="_input")],
                style=dict(display="flex", justifyContent="right")),
            _dcc_slider(key, init_cqm, with_suffix=True),])
for key, val in constraints.items()])

tour_titles = ["Set Legs", "Set Budget"]
leg_config = {
    "num_legs": "How Many:",
    "max_leg_length": "Longest Leg:",
    "min_leg_length": "Shortest Leg:",
    "max_leg_slope": "Steepest Leg:",
    "max_cost": "Highest Cost:",
    "max_time": "Longest Time:"}
leg_rows = [dbc.Row([
    f"{val}",
    dash.html.Br(),
    _dcc_input(key, init_tour, step=1) if key != "max_leg_slope" else
    _dcc_slider(key, init_tour, step=1, discrete_slider=True)])
    for key, val in leg_config.items()]
tour_config = dbc.Card(
    [dbc.Row([
        html.H4("Tour Settings", className="card-title", style={"textAlign": "left"})]),
     dbc.Row([
        dbc.Col([
            html.B(f"{tour_title}", style={"text-decoration": "underline"},) ])
                for tour_title in tour_titles]),
     dbc.Row([
        dbc.Col(leg_rows[:4], style={"margin-right": "20px"}),
        dbc.Col(leg_rows[4:], style={"margin-left": "20px"}),],)],
    body=True, color="secondary")

# Page-layout section
#####################

layout = [
    dbc.Row([
        dbc.Col([
            html.H1("Tour Planner", style={'textAlign': 'left'})], width=10),
        dbc.Col([
            html.Img(src="assets/ocean.png", height="50px", style={'textAlign': 'right'})], width=2)]),
    dbc.Row([
        dbc.Col(
            tour_config, width=4),
        dbc.Col(
            dbc.Card(constraint_card, body=True, color="secondary"), width=2),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    solver_card])]),
            ], width=2)],
        justify="left"),
    dbc.Tabs([
        dbc.Tab(tabs[tab], label=tab, tab_id=f"tab_{tab.lower()}",
            label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"},)
        for tab in tabs.keys()],
        id="tabs", active_tab="tab_graph")]

tips = [dbc.Tooltip(message, target=target) for target, message in tool_tips.items()]
layout.extend(tips)

app.layout = dbc.Container(layout, fluid=True,
    style={"backgroundColor": "black", "color": "rgb(6, 236, 220)"})

# Callbacks Section
###################

@app.callback(
    Output('space_graph', 'figure'),
    Output('time_graph', 'figure'),
    Output('diversity_graph', 'figure'),
    Output('problem_print_code', 'value'),
    Output('solutions_print_human', 'value'),
    Output('cqm_print', 'value'),
    Output('problem_print_human', 'value'),
    Output('input_print', 'value'),
    Output('max_leg_length', 'value'),
    Output('min_leg_length', 'value'),
    Output('weight_cost_slider', 'value'),
    Output('weight_cost_input', 'value'),
    Output('weight_time_slider', 'value'),
    Output('weight_time_input', 'value'),
    Output('weight_slope_slider', 'value'),
    Output('weight_slope_input', 'value'),
    Input('num_legs', 'value'),
    Input('max_leg_length', 'value'),
    Input('min_leg_length', 'value'),
    Input('max_leg_slope', 'value'),
    Input('max_cost', 'value'),
    Input('max_time', 'value'),
    Input('weight_cost_slider', 'value'),
    Input('weight_cost_input', 'value'),
    Input('weight_time_slider', 'value'),
    Input('weight_time_input', 'value'),
    Input('weight_slope_slider', 'value'),
    Input('weight_slope_input', 'value'),
    Input('problem_print_code', 'value'),
    Input('job_submit_state', 'children'),
    State('solutions_print_code', 'value'),)
def display(num_legs, max_leg_length, min_leg_length, max_leg_slope, max_cost,
    max_time, weight_cost_slider, weight_cost_input, weight_time_slider,
    weight_time_input, weight_slope_slider, weight_slope_input, problem_print_code,
    job_submit_state, solutions_print_code):
    """

    """
    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == 'max_leg_length' and max_leg_length <= min_leg_length:
        min_leg_length = max_leg_length
    if trigger_id == 'min_leg_length' and min_leg_length >= max_leg_length:
        max_leg_length = min_leg_length

    weights = ["cost", "time", "slope"]
    weight_vals = {}
    for weight in weights:
        weight_vals[weight] = dash.no_update
        if trigger_id == f'weight_{weight}_slider':
            weight_vals[weight] = eval(f'weight_{weight}_slider')
        if trigger_id == f'weight_{weight}_input':
            weight_vals[weight] = eval(f'weight_{weight}_input')

    if not trigger_id:
        legs = init_legs["legs"]
    elif trigger_id in [k for k in list(init_tour.keys()) if k not in ('max_cost', 'max_time')]:
        legs = set_legs(num_legs, [min_leg_length, max_leg_length], max_leg_slope)
    else:
        legs = json.loads(problem_print_code)

    solutions_print_human_val = dash.no_update
    samples = None
    if trigger_id == "job_submit_state":
        if in_job_submit_state(job_submit_state) == "COMPLETED":
            samples = get_samples(solutions_print_code)
            solutions_print_human_val = out_solutions_human(samples["sampleset"])

    inputs = {**init_tour, **init_cqm}
    for key in inputs.keys():
        inputs[key][2] = eval(key)

    cqm = build_cqm(legs, modes, max_cost, max_time, weight_cost_input,
                    weight_time_input, max_leg_slope, weight_slope_input)

    fig_diversity = dash.no_update
    fig_time = dash.no_update
    fig_space = plot_space(legs, samples)
    if samples:
        fig_time = plot_time(legs, transport, samples)
        fig_diversity = plot_diversity(legs, transport, samples)

    return fig_space, fig_time, fig_diversity, out_problem_code(legs), solutions_print_human_val, cqm.__str__(), \
        out_problem_human(legs), out_input_human(inputs, legs, transport), max_leg_length, \
        min_leg_length, weight_vals["cost"], weight_vals["cost"], weight_vals["time"], \
        weight_vals["time"], weight_vals["slope"], weight_vals["slope"]

job_bar = {'WAITING': [0, 'light'],
           'SUBMITTED': [25, 'info'],
           'PENDING': [50, 'warning'],
           'IN_PROGRESS': [75 ,'primary'],
           'COMPLETED': [100, 'success'],
           'CANCELLED': [100, 'info'],
           'FAILED': [100, 'danger'], }

@app.callback(
    Output('btn_solve_cqm', 'disabled'),
    Output('btn_cancel', component_property='style'),
    Output('wd_job', 'disabled'),
    Output('wd_job', 'interval'),
    Output('wd_job', 'n_intervals'),
    Output('bar_job_status', 'value'),
    Output('bar_job_status', 'color'),
    Output('job_submit_state', 'children'),
    Output('job_submit_time', 'children'),
    Output('job_elapsed_time', 'children'),
    Output('solutions_print_code', 'value'),
    Output('job_id', 'children'),
    Input('btn_solve_cqm', 'n_clicks'),
    Input('wd_job', 'n_intervals'),
    State('max_leg_slope', 'value'),
    State('max_cost', 'value'),
    State('max_time', 'value'),
    State('weight_cost_slider', 'value'),
    State('weight_cost_input', 'value'),
    State('weight_time_slider', 'value'),
    State('weight_time_input', 'value'),
    State('weight_slope_slider', 'value'),
    State('weight_slope_input', 'value'),
    State('problem_print_code', 'value'),
    State('job_submit_state', 'children'),
    State('job_submit_time', 'children'),
    State('job_id', 'children'),)
def cqm_submit(n_clicks, n_intervals, max_leg_slope, max_cost, max_time, weight_cost_slider, \
    weight_cost_input, weight_time_slider, weight_time_input, weight_slope_slider, \
    weight_slope_input, problem_print_code, job_submit_state, job_submit_time, job_id):
    """SM for job submission."""
    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if not trigger_id in ["btn_solve_cqm", "wd_job"]:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if trigger_id == "btn_solve_cqm":
        return True, dict(), False, 0.1*1000, 0, job_bar['WAITING'][0], \
            job_bar['WAITING'][1], out_job_submit_state("START"), datetime.datetime.now().strftime("%c"), \
            f"Elapsed: 0 sec.", dash.no_update, dash.no_update

    if in_job_submit_state(job_submit_state) == "START":
        # Need to disable all buttons
        job_submit_state = "SUBMITTED"
        solver = client.get_solver(supported_problem_types__issubset={"cqm"})
        legs = json.loads(problem_print_code)
        cqm = build_cqm(legs, modes, max_cost, max_time, weight_cost_input,
                            weight_time_input, max_leg_slope, weight_slope_input)
        problem_data_id = solver.upload_cqm(cqm).result()

        computation = solver.sample_cqm(problem_data_id,
                    label="Examples - Tour Planning", time_limit=5)
        submission_id = computation.wait_id()

        elapsed_time = (datetime.datetime.now() - datetime.datetime.strptime(job_submit_time, "%c")).seconds

        return True, dash.no_update, False, 1*1000, 0, job_bar['SUBMITTED'][0], \
            job_bar['SUBMITTED'][1], out_job_submit_state(job_submit_state), \
            dash.no_update, f"Elapsed: {elapsed_time} sec.", dash.no_update, submission_id

    if in_job_submit_state(job_submit_state) == "SUBMITTED":
        p = Problems(endpoint=client.endpoint, token=client.token)
        status = p.get_problem_status(job_id).status.value

        if status == None:   # First few checks
            job_submit_state = "SUBMITTED"
        else:
            job_submit_state = status

        elapsed_time = (datetime.datetime.now() - datetime.datetime.strptime(job_submit_time, "%c")).seconds

        return True, dash.no_update, False, 0.5*1000, 0, job_bar['SUBMITTED'][0], \
            job_bar['SUBMITTED'][1], out_job_submit_state(job_submit_state), \
            dash.no_update, f"Elapsed: {elapsed_time} sec.", dash.no_update, dash.no_update

    if in_job_submit_state(job_submit_state) in ['PENDING', 'IN_PROGRESS']:
        p = Problems(endpoint=client.endpoint, token=client.token)
        status = p.get_problem_status(job_id).status.value
        job_submit_state = status

        sampleset_str = "Failed maybe"
        hide_button = dash.no_update
        if status == 'IN_PROGRESS':
            hide_button = dict(display='none')
        elif status == 'COMPLETED':
            sampleset = client.retrieve_answer(job_id).sampleset
            sampleset_str = json.dumps(sampleset.to_serializable())

        elapsed_time = (datetime.datetime.now() - datetime.datetime.strptime(job_submit_time, "%c")).seconds

        return True, hide_button, False, 1*1000, 0, job_bar[status][0], \
            job_bar[status][1], out_job_submit_state(job_submit_state), \
            dash.no_update, f"Elapsed: {elapsed_time} sec.", sampleset_str, dash.no_update

    if in_job_submit_state(job_submit_state) in ['COMPLETED', 'CANCELLED', 'FAILED']:
        # Need to enable all buttons
        elapsed_time = (datetime.datetime.now() - datetime.datetime.strptime(job_submit_time, "%c")).seconds

        return False, dash.no_update, True, 0.1*1000, 0, dash.no_update, \
            dash.no_update, dash.no_update, \
            dash.no_update, f"Elapsed: {elapsed_time} sec.", dash.no_update, dash.no_update

if __name__ == "__main__":
    app.run_server(debug=True)
