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

import dimod
from dwave.cloud.hybrid import Client
from dwave.cloud.api import Problems

modes = transport.keys()  # global
num_modes = len(modes)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

try:
    client = Client.from_config(profile="test")
except Exception as client_err:
    client = None

constraints = ["Cost", "Time", "Slope"]
constraint_card = [html.H4("CQM Settings", className="card-title")]
constraint_card.extend([
    html.Div([
        dbc.Label(f"{constraint} Weight"),
        html.Div([
            dcc.Input(id=f'weight_{constraint.lower()}_input', type='number',
                min=init_cqm[f'weight_{constraint.lower()}_input'][0],
                max=init_cqm[f'weight_{constraint.lower()}_input'][1], step=1,
                value=init_cqm[f'weight_{constraint.lower()}_input'][2])],
                style=dict(display='flex', justifyContent='right')),
            dcc.Slider(init_cqm[f'weight_{constraint.lower()}_input'][0],
                init_cqm[f'weight_{constraint.lower()}_input'][1],
                id=f'weight_{constraint.lower()}_slider',
                marks={init_cqm[f'weight_{constraint.lower()}_input'][0]:
                        {"label": "Soft", "style": {'color': 'white'}},
                    init_cqm[f'weight_{constraint.lower()}_input'][1]:
                        {"label": "Hard", "style": {'color': 'white'}}},
                value=init_cqm[f'weight_{constraint.lower()}_input'][2],),])
            for constraint in constraints])

tour_titles = ["Set Legs", "Set Budget"]
leg_settings = [["How Many:", "num_legs"],["Longest Leg:", "max_leg_length"],
                ["Shortest Leg:", "min_leg_length"],
                ["Highest Cost:", "max_cost"], ["Longest Time:", "max_time"]]
leg_setting_rows = [dbc.Row([
    f"{leg_setting[0]}",
    html.Br(),
    dcc.Input(id=f"{leg_setting[1]}", type='number', min=init_tour[f"{leg_setting[1]}"][0],
        max=init_tour[f"{leg_setting[1]}"][1], step=1,
        value=init_tour[f"{leg_setting[1]}"][2])]) for leg_setting in leg_settings[:3]]
leg_setting_rows.append(dbc.Row([
    "Steepest Leg:",
    dash.html.Br(),
    dcc.Slider(min=0, max=10, step=1,
        marks={i: {"label": f'{str(i)}', "style": {'color': 'white'}} for i in
        range(init_tour['max_leg_slope'][0], init_tour['max_leg_slope'][1] + 1, 2)},
        value=init_tour['max_leg_slope'][2], id='max_leg_slope'),]))
leg_constraint_rows = [dbc.Row([
    f"{leg_constraint[0]}",
    html.Br(),
    dcc.Input(id=f"{leg_constraint[1]}", type='number', min=init_tour[f"{leg_constraint[1]}"][0],
        max=init_tour[f"{leg_constraint[1]}"][1], step=1,
        value=init_tour[f"{leg_constraint[1]}"][2])]) for leg_constraint in leg_settings[3:]]

tour_config = dbc.Card(
    [dbc.Row([
        html.H4("Tour Settings", className="card-title", style={'textAlign': 'left'})]),
     dbc.Row([
        dbc.Col([
            html.B(f"{tour_title}", style={"text-decoration": "underline"},) ])
                for tour_title in tour_titles]),
     dbc.Row([
        dbc.Col(leg_setting_rows, style={'margin-right': '20px'}),
        dbc.Col(leg_constraint_rows, style={'margin-left': '20px'}),],)],
    body=True, color="secondary")

graphs = ["Space", "Time", "Diversity"]
graph_card = dbc.Tabs([
    dbc.Tab(dbc.Card([
        dbc.Row([
            dbc.Col(
                dcc.Graph(id=f'{graph.lower()}_graph'), width=12)])]), label=f"{graph}",
                    tab_id=f"graph_{graph.lower()}",
                    label_style={"color": "white", "backgroundColor": "black"},)
    for graph in graphs])

solver_card = dbc.Card([
    html.H4("Job Submission", className="card-title"),
    dbc.Col([
        dbc.Button("Solve CQM", id="btn_solve_cqm", color="primary", className="me-1"),
        dcc.Interval(id='check_job_status', interval=None, n_intervals=0, disabled=True, max_intervals=1),
        dbc.Progress(id="job_status_progress", value=0, color="info", className="mb-3"),
        html.P(id='job_submit_state', children=out_job_submit_state('READY')),   # if no client change ready
        html.P(id='job_submit_time', children='Mon Sep 26 07:39:20 2022', style = dict(display='none')),
        html.P(id='job_problem_id', children='4e07426f-a0d1-4616-8e1c-c49b3ce542d8', style = dict(display='none')),
        html.P(id='job_elapsed_time', children=f""),
        dbc.Button("Cancel Job", id="btn_cancel", color="warning", className="me-1",
            style = dict(display='none')),]),],
    color="secondary")

initital_views = {"problem": out_problem_code(init_legs),
                  "solutions": "SampleSet object to be displayed here",}
viewers = ["problem", "solutions", ]
readers = ["Human", "Code"]
viewer_tabs = {}
for viewer in viewers:
    viewer_tabs[viewer] = dbc.Tabs([
        dbc.Tab(dbc.Card([
                    dbc.Row([
                        dbc.Col([
                            dcc.Textarea(id=f"{viewer}_print_{reader.lower()}", value='',
                                style={'width': '100%'}, rows=20)])]),]), label=f"{reader} Readable",
                                    tab_id=f"tab_{viewer}_print_{reader.lower()}",
                                    label_style={"color": "white", "backgroundColor": "black"},)
    for reader in readers])

initital_views = {"cqm": "", "input": "", "transport": out_transport_human(transport)}
viewers = ["cqm", "input", "transport"]
viewer_cards = {}
for viewer in viewers:
    viewer_cards[viewer] = dbc.Card([
        dbc.Row([
            dbc.Col([
                dcc.Textarea(id=f"{viewer}_print", value=initital_views[viewer],
                    style={'width': '100%'}, rows=20)])]),])

app.layout = dbc.Container([
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
            dbc.Tab(graph_card, label="Graph", tab_id="tab_graph",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"},),
            dbc.Tab(viewer_tabs["problem"], label="Problem", tab_id="tab_problem",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(viewer_cards["cqm"], label="CQM", tab_id="tab_cqm",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(viewer_tabs["solutions"], label="Solutions", tab_id="tab_solutions",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(viewer_cards["input"], label="Inputs", tab_id="tab_inputs",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(viewer_cards["transport"], label="Transport", tab_id="tab_transport",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"})],
            id="tabs", active_tab="tab_graph"),

    dbc.Tooltip("Number of legs for the tour.",
                target="num_legs",),
    dbc.Tooltip("Maximum length for a single leg.",
                target="max_leg_length",),
    dbc.Tooltip("Minimum length for a single leg.",
                target="min_leg_length",),
    dbc.Tooltip("Maximum elevation for a single leg.",
                target="max_leg_slope",),],
    fluid=True, style={"backgroundColor": "black", "color": "rgb(6, 236, 220)"})

@app.callback(
    Output('space_graph', 'figure'),
    Output('time_graph', 'figure'),
    Output('diversity_graph', 'figure'),
    Output('problem_print_code', 'value'),
    Output('solutions_print_human', 'value'),
    Output('cqm_print', 'value'),
    #Output('cqm_print_code', 'value'),
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
    Output('check_job_status', 'disabled'),
    Output('check_job_status', 'interval'),
    Output('check_job_status', 'n_intervals'),
    Output('job_status_progress', 'value'),
    Output('job_status_progress', 'color'),
    Output('job_submit_state', 'children'),
    Output('job_submit_time', 'children'),
    Output('job_elapsed_time', 'children'),
    Output('solutions_print_code', 'value'),
    Output('job_problem_id', 'children'),
    Input('btn_solve_cqm', 'n_clicks'),
    Input('check_job_status', 'n_intervals'),
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
    State('job_problem_id', 'children'),)
def cqm_submit(n_clicks, n_intervals, max_leg_slope, max_cost, max_time, weight_cost_slider, \
    weight_cost_input, weight_time_slider, weight_time_input, weight_slope_slider, \
    weight_slope_input, problem_print_code, job_submit_state, job_submit_time, job_problem_id):
    """SM for job submission."""
    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if not trigger_id in ["btn_solve_cqm", "check_job_status"]:
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
        status = p.get_problem_status(job_problem_id).status.value

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
        status = p.get_problem_status(job_problem_id).status.value
        job_submit_state = status

        sampleset_str = "Failed maybe"
        hide_button = dash.no_update
        if status == 'IN_PROGRESS':
            hide_button = dict(display='none')
        elif status == 'COMPLETED':
            sampleset = client.retrieve_answer(job_problem_id).sampleset
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
