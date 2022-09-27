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

from formatting import out_job_submit_state, in_job_submit_state, out_problem_code, out_problem_human, in_problem_code
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

def budgets(legs):
    legs_total = sum(l["length"] for l in legs)
    costs = [c["Cost"] for c in transport.values()]
    speeds = [s["Speed"] for s in transport.values()]
    max_cost = round(legs_total * np.mean([min(costs), max(costs)]))
    max_time = round(legs_total * np.mean([min(speeds), max(speeds)]))

    return max_cost, max_time

init_cqm = {'weight_cost_input': [0, 10000, 100],
    'weight_time_input': [0, 10000, 30],
    'weight_slope_input': [0, 10000, 150],}

init_tour = {'num_legs': [5, 100, 10],
    'max_leg_length': [1, 20, 10],
    'min_leg_length': [1, 20, 2],
    'max_leg_slope': [0, 10, 8],
    'max_cost': [0, 100000, 0],
    'max_time': [0, 100000, 0],}

init_legs = {'legs': set_legs(init_tour['num_legs'][2],
    [init_tour['min_leg_length'][2], init_tour['max_leg_length'][2]],
    init_tour['max_leg_slope'][2])}

init_tour['max_cost'][2], init_tour['max_time'][2] = budgets(init_legs['legs'])

cqm_config = dbc.Card(
    [html.H4("CQM Settings", className="card-title"),
     html.Div([dbc.Label("Cost Weight"),
               html.Div([dcc.Input(id='weight_cost_input', type='number',
                min=init_cqm['weight_cost_input'][0], max=init_cqm['weight_cost_input'][1],
                step=1, value=init_cqm['weight_cost_input'][2])],
               style=dict(display='flex', justifyContent='right')),
               dcc.Slider(init_cqm['weight_cost_input'][0], init_cqm['weight_cost_input'][1],
                id='weight_cost_slider', marks={init_cqm['weight_cost_input'][0]:
                {"label": "Soft", "style": {'color': 'white'}}, init_cqm['weight_cost_input'][1]:
                {"label": "Hard", "style": {'color': 'white'}}}, value=init_cqm['weight_cost_input'][2],),]),
     html.Div([dbc.Label("Time Weight"),
               html.Div([dcc.Input(id='weight_time_input', type='number',
                min=init_cqm['weight_time_input'][0], max=init_cqm['weight_time_input'][1],
                step=1, value=init_cqm['weight_time_input'][2])],
                style=dict(display='flex', justifyContent='right')),
               dcc.Slider(init_cqm['weight_time_input'][0], init_cqm['weight_time_input'][1],
                id='weight_time_slider', marks={init_cqm['weight_time_input'][0]:
                {"label": "Soft", "style": {'color': 'white'}}, init_cqm['weight_time_input'][1]:
                {"label": "Hard", "style": {'color': 'white'}}}, value=init_cqm['weight_time_input'][2],),]),
     html.Div([dbc.Label("Slope Weight"),
               html.Div([dcc.Input(id='weight_slope_input', type='number',
                min=init_cqm['weight_slope_input'][0], max=init_cqm['weight_slope_input'][1],
                step=1, value=init_cqm['weight_slope_input'][2])],
                style=dict(display='flex', justifyContent='right')),
               dcc.Slider(init_cqm['weight_slope_input'][0], init_cqm['weight_slope_input'][1],
                id='weight_slope_slider', marks={init_cqm['weight_slope_input'][0]:
                {"label": "Soft", "style": {'color': 'white'}}, init_cqm['weight_slope_input'][1]:
                {"label": "Hard", "style": {'color': 'white'}}}, value=init_cqm['weight_slope_input'][2],),]),],
    body=True, color="secondary")

tour_config = dbc.Card(
    [dbc.Row([
        html.H4("Tour Settings", className="card-title", style={'textAlign': 'left'})]),
     dbc.Row([
        dbc.Col([
            html.B("Set Legs", style={"text-decoration": "underline"},)]),
        dbc.Col([
            html.B("Set Budget", style={"text-decoration": "underline"}),]),]),
     dbc.Row([
        dbc.Col([
            dbc.Row([
                "How Many:",]),
            dbc.Row([
                dcc.Input(id='num_legs', type='number', min=init_tour['num_legs'][0],
                    max=init_tour['num_legs'][1], step=1, value=init_tour['num_legs'][2])],),
            dbc.Row([
                "Longest Leg:",]),
            dbc.Row([
                dcc.Input(id='max_leg_length', type='number', min=init_tour['max_leg_length'][0],
                    max=init_tour['max_leg_length'][1], step=1, value=init_tour['max_leg_length'][2]),]),
            dbc.Row([
                "Shortest Leg:"]),
            dbc.Row([
               dcc.Input(id='min_leg_length', type='number', min=init_tour['min_leg_length'][0],
                    max=init_tour['min_leg_length'][1], step=1,
                    value=init_tour['min_leg_length'][2]),]),
            dbc.Row([
               "Steepest Leg:",]),
            dbc.Row([
               dcc.Slider(min=0, max=10, step=1,
                    marks={i: {"label": f'{str(i)}', "style": {'color': 'white'}} for i in
                    range(init_tour['max_leg_slope'][0], init_tour['max_leg_slope'][1] + 1, 2)},
                    value=init_tour['max_leg_slope'][2], id='max_leg_slope'),]),],
                    style={'margin-right': '20px'}),
        dbc.Col([
            dbc.Row([
                "Highest Cost:",]),
            dbc.Row([
               dcc.Input(id='max_cost', type='number', min=init_tour['max_cost'][0],
                    max=init_tour['max_cost'][1], step=1, value=init_tour['max_cost'][2]),]),
            dbc.Row([
                "Longest Time:",]),
            dbc.Row([
               dcc.Input(id='max_time', type='number', min=init_tour['max_time'][0],
                    max=init_tour['max_time'][1], step=1, value=init_tour['max_time'][2]),]),],
                    style={'margin-left': '20px'}),],)],
    body=True, color="secondary")

graph_card = dbc.Card([
    html.H4("Tour Legs", className="card-title"),
    dbc.Col(
        dcc.Graph(id='tour_graph'), width=12),],
    color="secondary")

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

problem_viewer = dbc.Tabs([
    dbc.Tab(dbc.Card([
                dbc.Row([
                    dbc.Col([
                        dcc.Textarea(id="problem_print_human", value='Human Readable',
                            style={'width': '100%'}, rows=20)])]),]), label="Human Readable",
                                tab_id="tab_problem_print_human",
                                label_style={"color": "white", "backgroundColor": "black"},),
    dbc.Tab(dbc.Card([
                dbc.Row([
                    dbc.Col([
                        dcc.Textarea(id="problem_print_code", value=out_problem_code(init_legs),
                            style={'width': '100%'}, rows=20)])]),]), label="Computer Readable",
                                tab_id="tab_problem_print_code",
                                label_style={"color": "white", "backgroundColor": "black"},),])

cqm_viewer = dbc.Tabs([
    dbc.Tab(dbc.Card([
                dbc.Row([
                    dbc.Col([
                        dcc.Textarea(id="cqm_print_human", value='Human Readable',
                            style={'width': '100%'}, rows=20)])]),]), label="Human Readable",
                                tab_id="tab_cqm_print_human",
                                label_style={"color": "white", "backgroundColor": "black"},),
    dbc.Tab(dbc.Card([
                dbc.Row([
                    dbc.Col([
                        dcc.Textarea(id="cqm_print_code", value='Computer Readable',
                            style={'width': '100%'}, rows=20)])]),]), label="Computer Readable",
                                tab_id="tab_cqm_print_code",
                                label_style={"color": "white", "backgroundColor": "black"},),])

solutions_viewer = dbc.Tabs([
    dbc.Tab(dbc.Card([
                dbc.Row([
                    dbc.Col([
                        dcc.Textarea(id="solutions_print_human", value='Your solutions',
                            style={'width': '100%'}, rows=20)])]),]), label="Human Readable",
                                tab_id="tab_solutions_print_human",
                                label_style={"color": "white", "backgroundColor": "black"},),
    dbc.Tab(dbc.Card([
                dbc.Row([
                    dbc.Col([
                        dcc.Textarea(id="solutions_print_code", value='Computer Readable',
                            style={'width': '100%'}, rows=20)])]),]), label="Computer Readable",
                                tab_id="tab_solutions_print_code",
                                label_style={"color": "white", "backgroundColor": "black"},),])

inputs_viewer = dbc.Card([
    dbc.Row([
        dbc.Col([
            dcc.Textarea(id="input_print", value='Some inputs have dynamically set boundaries\n',
                style={'width': '100%'}, rows=20)])]),]),

transport_viewer = dbc.Card([
    dbc.Row([
        dbc.Col([
            dcc.Textarea(id="transport_print", value=json.dumps(transport),
                style={'width': '100%'}, rows=20)])]),]),

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
            cqm_config, width=2),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    solver_card])]),
            ], width=2)],
        justify="left"),

    dbc.Tabs([
            dbc.Tab(graph_card, label="Graph", tab_id="tab_graph",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"},),
            dbc.Tab(problem_viewer, label="Problem", tab_id="tab_problem",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(cqm_viewer, label="CQM", tab_id="tab_cqm",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(solutions_viewer, label="Solutions", tab_id="tab_solutions",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(inputs_viewer, label="Inputs", tab_id="tab_inputs",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(transport_viewer, label="Transport", tab_id="tab_transport",
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

def calculate_total(t, measure, legs, num_legs):
    if measure == 'Exercise':
        return dimod.quicksum(t[i]*transport[t[i].variables[0].split('_')[0]]['Exercise']*legs[i//num_modes]['length']*legs[i//num_modes]['uphill'] for i in range(num_modes*num_legs))
    elif measure == 'Time':
        return dimod.quicksum(t[i]*legs[i//num_modes]['length']/transport[t[i].variables[0].split('_')[0]]['Speed'] for i in range(num_modes*num_legs))
    else:
        return dimod.quicksum(t[i]*transport[t[i].variables[0].split('_')[0]][measure]*legs[i//num_modes]['length'] for i in range(num_modes*num_legs))

@app.callback(
    Output('tour_graph', 'figure'),
    Output('problem_print_code', 'value'),
    Output('cqm_print_human', 'value'),
    Output('cqm_print_code', 'value'),
    Output('problem_print_human', 'value'),    # temp so I can use solutions_print elsewhere
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

    for weight in ["cost", "time", "slope"]:
        exec(f"""
if trigger_id == 'weight_{weight}_slider':
        weight_{weight} = weight_{weight}_slider
else:
    weight_{weight} = weight_{weight}_input
""".format(weight))

    if not trigger_id:
        legs = init_legs["legs"]
    elif trigger_id in [k for k in list(init_tour.keys()) if k not in ('max_cost', 'max_time')]:
        legs = set_legs(num_legs, [min_leg_length, max_leg_length], max_leg_slope)
    else:
        legs = json.loads(problem_print_code)

    inputs = {**init_tour, **init_cqm}
    for key in inputs.keys():
        inputs[key][2] = eval(key)

    cqm = build_cqm(legs, modes, max_cost, max_time, weight_cost_input,
                    weight_time_input, max_leg_slope, weight_slope_input)

    df_legs = pd.DataFrame({'Length': [l['length'] for l in legs],
                            'Slope': [s['uphill'] for s in legs]})
    df_legs["Tour"] = 0
    fig = px.bar(df_legs, x="Length", y='Tour', color="Slope", orientation="h",
                 color_continuous_scale=px.colors.diverging.Geyser)

    if trigger_id == "job_submit_state":
        if in_job_submit_state(job_submit_state) == "COMPLETED":

            result = dimod.SampleSet.from_serializable(in_problem_code(solutions_print_code))
            sampleset_feasible = result.filter(lambda row: row.is_feasible)
            first = sorted({int(key.split('_')[1]): key.split('_')[0] for key,val in sampleset_feasible.first.sample.items() if val==1.0}.items())
            fig = px.bar(df_legs, x="Length", y='Tour', color="Slope", orientation="h",
                         color_continuous_scale=px.colors.diverging.Geyser, text=[transport for leg,transport in first])

            x_pos = 0
            for leg, icon in first:
                fig.add_layout_image(dict(source=f"assets/{icon}.png", xref="x",
                    yref="y", x=x_pos, y=-0.1, sizex=2, sizey=2, opacity=1,
                    layer="above"))
                x_pos += df_legs["Length"][leg]

    fig.add_layout_image(
            dict(source="assets/europe.png", xref="x", yref="y", x=0, y=0.5,
                 sizex=df_legs["Length"].sum(), sizey=1, sizing="stretch",
                 opacity=0.25, layer="below"))

    x_pos = 0
    for indx, leg in enumerate(legs):
        if leg['toll']:
            fig.add_layout_image(dict(source=f"assets/toll.png", xref="x",
                yref="y", x=x_pos, y=0.2, sizex=2, sizey=2, opacity=1, layer="above"))
        x_pos += df_legs["Length"][indx]

    fig.update_xaxes(showticklabels=True, title="Distance")
    fig.update_yaxes(showticklabels=False, title=None, range=(-0.5, 0.5))
    fig.update_traces(width=.1)
    fig.update_layout(font_color="rgb(6, 236, 220)", margin=dict(l=20, r=20, t=20, b=20),
                      paper_bgcolor="rgba(0,0,0,0)")

    return fig, out_problem_code(legs), cqm.__str__(), "CQM", out_problem_human(legs), \
        json.dumps(inputs), max_leg_length, min_leg_length, weight_cost_slider, \
        weight_cost_input, weight_time_slider, weight_time_input, weight_slope_slider, \
        weight_slope_input

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
