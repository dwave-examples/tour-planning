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
import plotly.express as px
import pandas as pd
import random
import numpy as np
from pprint import pprint
import time

from tour_planning import job_submission, tour, model
from tour_planning import build_cqm

import dimod
from dwave.cloud.hybrid import Client

transport = {
    'walk': {'Speed': 1, 'Cost': 0, 'Exercise': 1},
    'cycle': {'Speed': 3, 'Cost': 2, 'Exercise': 2},
     'bus': {'Speed': 4, 'Cost': 3, 'Exercise': 0},
     'drive': {'Speed': 7, 'Cost': 5, 'Exercise': 0}}
modes = transport.keys()  # global
num_modes = len(modes)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

model = model()
tour = tour()
job_tracker = job_submission(profile='test')

cqm_config = dbc.Card(
    [html.H4("CQM Settings", className="card-title"),
     html.Div([dbc.Label("Cost Weight"),
               html.Div([dcc.Input(id='weight_cost_input', type='number', min=0,
                    max=10000, step=1, value=100)],
               style=dict(display='flex', justifyContent='right')),
               dcc.Slider(0, 10000, id='weight_cost_slider',
                     marks={0: {"label": "Soft", "style": {'color': 'white'}},
                            10000: {"label": "Hard", "style": {'color': 'white'}}}, value=100,),]),
     html.Div([dbc.Label("Time Weight"),
               html.Div([dcc.Input(id='weight_time_input', type='number', min=0,
                    max=10000, step=1, value=30)],
               style=dict(display='flex', justifyContent='right')),
               dcc.Slider(0, 10000, id='weight_time_slider',
                     marks={0: {"label": "Soft", "style": {'color': 'white'}},
                            10000: {"label": "Hard", "style": {'color': 'white'}}}, value=30,),]),
     html.Div([dbc.Label("Slope Weight"),
               html.Div([dcc.Input(id='weight_slope_input', type='number', min=0,
                    max=10000, step=1, value=150)],
               style=dict(display='flex', justifyContent='right')),
               dcc.Slider(0, 10000, id='weight_slope_slider',
                     marks={0: {"label": "Soft", "style": {'color': 'white'}},
                            10000: {"label": "Hard", "style": {'color': 'white'}}}, value=150,),]),],
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
                dcc.Input(id='num_legs', type='number', min=5, max=100, step=1, value=10)],),
            dbc.Row([
                "Longest Leg:",]),
            dbc.Row([
                dcc.Input(id='max_leg_length', type='number', min=2, max=20,
                          step=1, value=10),]),
            dbc.Row([
                "Shortest Leg:"]),
            dbc.Row([
               dcc.Input(id='min_leg_length', type='number', min=1, max=19,
                         step=1, value=2),]),
            dbc.Row([
               "Steepest Leg:",]),
            dbc.Row([
               dcc.Slider(min=0, max=10, step=1,
                          marks={i: {"label": f'{str(i)}',
                                     "style": {'color': 'white'}} for i in range(0, 11, 2)},
                          value=8, id='max_leg_slope'),]),], style={'margin-right': '20px'}),
        dbc.Col([
            dbc.Row([
                "Highest Cost:",]),
            dbc.Row([
               dcc.Input(id='max_cost', type='number', min=tour.max_cost_min,
                    max=tour.max_cost_max, step=1, value=tour.max_cost),]),
            dbc.Row([
                "Longest Time:",]),
            dbc.Row([
               dcc.Input(id='max_time', type='number', min=tour.max_time_min,
                    max=tour.max_time_max, step=1, value=tour.max_time),]),], style={'margin-left': '20px'}),],)],
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
        html.P(id='job_status', children=''),]),],
    color="secondary")

cqm_viewer = dbc.Card([
    dbc.Row([
        dbc.Col([
            dcc.Textarea(id="cqm_print", value='Your CQM',
                style={'width': '100%'}, rows=20)])]),]),

solutions_viewer = dbc.Card([
    dbc.Row([
        dbc.Col([
            dcc.Textarea(id="solutions_print", value='Your solutions',
                style={'width': '100%'}, rows=20)])]),]),

app.layout = dbc.Container([
    html.H1("Tour Planner", style={'textAlign': 'left'}),
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
            dbc.Tab(cqm_viewer, label="CQM", tab_id="tab_cqm",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),
            dbc.Tab(solutions_viewer, label="Solutions", tab_id="tab_solutions",
                label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"}),],
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
    Output('cqm_print', 'value'),
    Output('solutions_print', 'value'),
    # Output('num_legs', 'value'),
    # Output('max_leg_length', 'value'),
    # Output('min_leg_length', 'value'),
    # Output('max_leg_slope', 'value'),
    # Output('max_cost', 'value'),
    # Output('max_time', 'value'),
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
    Input('job_status_progress', 'color'),)
def display(num_legs, max_leg_length, min_leg_length, max_leg_slope, max_cost,
    max_time, weight_cost_slider, weight_cost_input, weight_time_slider,
    weight_time_input, weight_slope_slider, weight_slope_input, job_status_progress):
    """

    """
    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == 'max_leg_length' and max_leg_length < min_leg_length + 1:
        min_leg_length = max_leg_length - 1
    if trigger_id == 'min_leg_length' and min_leg_length > max_leg_length - 1:
        max_leg_length = min_leg_length + 1

    for weight in ["cost", "time", "slope"]:
        exec(f"""
if trigger_id == 'weight_{weight}_slider':
        weight_{weight} = weight_{weight}_slider
else:
    weight_{weight} = weight_{weight}_input
""".format(weight))

    # Calculate tour

    legs = [{'length': round((max_leg_length - min_leg_length)*random.random() + min_leg_length, 1),
             'uphill': round(max_leg_slope*random.random(), 1),
             'toll': np.random.choice([True, False], 1, p=[0.2, 0.8])[0]} for i in range(num_legs)]

    max_cost_min = round(sum(l["length"] for l in legs)*min([c["Cost"] for c in transport.values()]))
    max_cost_max = round(sum(l["length"] for l in legs)*max([c["Cost"] for c in transport.values()]))

    max_time_max = round(sum(l["length"] for l in legs)/min(s["Speed"] for s in transport.values()))
    max_time_min = round(sum(l["length"] for l in legs)/max(s["Speed"] for s in transport.values()))

    # Calculate CQM

    t= [dimod.Binary(f'{mode}_{i}') for i in range(num_legs) for mode in transport.keys()]

    cqm = dimod.ConstrainedQuadraticModel()
    cqm.set_objective(-calculate_total(t, "Exercise", legs, num_legs))

    for leg in range(num_legs):
        cqm.add_constraint(dimod.quicksum(t[num_modes*leg:num_modes*leg+num_modes]) == 1, label=f"One-hot leg{leg}")
    cqm.add_constraint(calculate_total(t, "Cost", legs, num_legs) <= max_cost, label="Total cost", weight=weight_cost_input, penalty='quadratic')
    cqm.add_constraint(calculate_total(t, "Time", legs, num_legs) <= max_time, label="Total time", weight=weight_time_input, penalty='linear')

    drive_index = list(modes).index('drive')
    cycle_index = list(modes).index('cycle')
    for leg in range(num_legs):
         if legs[leg]['toll']:
             cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][drive_index] == 0, label=f"Toll to drive on leg {leg}")
         if legs[leg]['uphill'] > max_leg_slope/2:
             cqm.add_constraint(t[num_modes*leg:num_modes*leg+num_modes][cycle_index] == 0, label=f"Too steep to cycle on leg {leg}", weight=weight_slope_input)

    # Create graph

    df_legs = pd.DataFrame({'Length': [l['length'] for l in legs],
                            'Slope': [s['uphill'] for s in legs]})
    df_legs["Tour"] = 0
    fig = px.bar(df_legs, x="Length", y='Tour', color="Slope", orientation="h",
                 color_continuous_scale=px.colors.diverging.Geyser)

    if "job_status_progress" == trigger_id:
        if color == "success":
            sampleset_feasible = job_tracker.result.filter(lambda row: row.is_feasible)
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
            dict(source="assets/map.png", xref="x", yref="y", x=0, y=0.5,
                 sizex=df_legs["Length"].sum(), sizey=1, sizing="stretch",
                 opacity=0.75, layer="below"))

    x_pos = 0
    for indx, leg in enumerate(tour.legs):
        if leg['toll']:
            fig.add_layout_image(dict(source=f"assets/toll.png", xref="x",
                yref="y", x=x_pos, y=0.2, sizex=2, sizey=2, opacity=1, layer="above"))
        x_pos += df_legs["Length"][indx]

    fig.update_xaxes(showticklabels=True, title="Distance")
    fig.update_yaxes(showticklabels=False, title=None, range=(-0.5, 0.5))
    fig.update_traces(width=.1)
    fig.update_layout(font_color="rgb(6, 236, 220)", margin=dict(l=20, r=20, t=20, b=20),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig, cqm.__str__(), "solutions printed here",weight_cost_slider, \
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
    Output('check_job_status', 'disabled'),
    Output('check_job_status', 'interval'),
    Output('check_job_status', 'n_intervals'),
    Output('job_status_progress', 'value'),
    Output('job_status_progress', 'color'),
    Output('job_status', 'children'),
    Input('btn_solve_cqm', 'n_clicks'),
    Input('check_job_status', 'n_intervals'),)
def cqm_submit(n_clicks, n_intervals):
    """SM for job submission."""
    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if not trigger_id in ["btn_solve_cqm", "check_job_status"]:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if trigger_id == "btn_solve_cqm":
        job_tracker.submission_time = time.time()
        return True, False, 0.1*1000, 0, job_bar['WAITING'][0], job_bar['WAITING'][1], dash.no_update

    if job_tracker.state == "READY":
        job_tracker.state = "SUBMITTED"
        job_tracker.computation = None
        job_tracker.client = Client.from_config(profile="test")
        solver = job_tracker.client.get_solver(supported_problem_types__issubset={"cqm"})
        job_tracker.problem_data_id = solver.upload_cqm(model.cqm).result()
        job_tracker.computation = solver.sample_cqm(job_tracker.problem_data_id,
                    label="Examples - Tour Planning", time_limit=5)

        elapsed_time = round(time.time() - job_tracker.submission_time)
        return True, False, 1*1000, 0, job_bar['SUBMITTED'][0], job_bar['SUBMITTED'][1], html.P([f"Status: {job_tracker.status}",html.Br(),f"Elapsed: {elapsed_time} sec."])

    if job_tracker.state in ["SUBMITTED", "RUNNING"]:
        job_tracker.status = job_tracker.computation.remote_status

        if job_tracker.status == None:   # First few checks
            job_tracker.state = "SUBMITTED"
            elapsed_time = round(time.time() - job_tracker.submission_time)
            return True, False, 0.5*1000, 0, job_bar['SUBMITTED'][0], job_bar['SUBMITTED'][1], html.P([f"Status: {job_tracker.status}",html.Br(),f"Elapsed: {elapsed_time} sec."])

        if job_tracker.status in ['PENDING', 'IN_PROGRESS']:
            job_tracker.state = "RUNNING"
            elapsed_time = round(time.time() - job_tracker.submission_time)
            return True, False, 1*1000, 0, job_bar[job_tracker.status][0], job_bar[job_tracker.status][1], html.P([f"Status: {job_tracker.status}",html.Br(),f"Elapsed: {elapsed_time} sec."])

        if job_tracker.status in ['COMPLETED', 'CANCELLED', 'FAILED']:
            job_tracker.state = "DONE"
            if job_tracker.status == 'COMPLETED':
                job_tracker.result = job_tracker.computation.sampleset
            elapsed_time = round(time.time() - job_tracker.submission_time)
            return True, False, 1*1000, 0, job_bar[job_tracker.status][0], job_bar[job_tracker.status][1], html.P([f"Status: {job_tracker.status}",html.Br(),f"Elapsed: {elapsed_time} sec."])

    if job_tracker.state == "DONE":
        job_tracker.state = "READY"
        elapsed_time = round(time.time() - job_tracker.submission_time)
        job_tracker.client.close()
        return False, True, 0.1*1000, 0, dash.no_update, dash.no_update, html.P([f"Status: {job_tracker.status}",html.Br(),f"Elapsed: {elapsed_time} sec."])

if __name__ == "__main__":
    app.run_server(debug=True)
