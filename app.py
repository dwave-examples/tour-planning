import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import random
import numpy as np
from pprint import pprint

from tour_planning import build_cqm, solve_cqm
from dwave.system import LeapHybridCQMSampler

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


class tour():
    """

    """
    def __init__(self):
        self.num_legs = 10
        self.max_length = 10
        self.min_length = 2
        self.max_elevation = 8
        self.transport = {
            'walk': {'Speed': 1, 'Cost': 0, 'Exercise': 1},
            'cycle': {'Speed': 3, 'Cost': 2, 'Exercise': 2},
             'bus': {'Speed': 4, 'Cost': 3, 'Exercise': 0},
             'drive': {'Speed': 7, 'Cost': 5, 'Exercise': 0}}
        self.update_config()

    def update_config(self):
        self.legs = [{'length': round((self.max_length - self.min_length)*random.random() + self.min_length, 1),
                 'uphill': round(self.max_elevation*random.random(), 1),
                 'toll': np.random.choice([True, False], 1, p=[0.2, 0.8])[0]} for i in range(self.num_legs)]

        self.max_cost = sum(l["length"] for l in self.legs)*np.mean([c["Cost"] for c in self.transport.values()])
        self.max_time = 0.5*sum(l["length"] for l in self.legs)/min(s["Speed"] for s in self.transport.values())

        self.modes = self.transport.keys()
        self.num_modes = len(self.modes)

tour = tour()

cqm_config = dbc.Card(
    [html.H4("CQM Settings", className="card-title"),
     html.Div([dbc.Label("X variable"),
               dcc.Dropdown(id="x-variable",
                   options=[{"label": str(col), "value": col} for col in [1, 3, 5, 7]],
                   value=3,),]),
     html.Div([dbc.Label("Y variable"),
               dcc.Dropdown(id="y-variable",
                   options=[{"label": col, "value": col} for col in ["abc", "def"]],
                   value="sepal length (cm)",),]),
     html.Br(),
     html.Label('Slider'),
     dcc.Slider(min=0, max=9, step=None, marks={i: f'{str(i)}' for i in range(0, 9)},
                value=5, id='slider1'),
     html.Label('Text Input'),
     dcc.Input(id="test2", value='MTL', type='text'),],
    body=True, color="secondary")

tour_config = dbc.Card(
    [dbc.Row([
        html.H4("Tour Settings", className="card-title"),
        dbc.Col([
            html.B("Legs"),
            html.Br(),
            dcc.Input(id='num_legs', type='number', min=5, max=100, step=1, value=10)],
        width=5),
        dbc.Col([
            html.B("Leg Description"),
            dbc.Row([
                "Max. Length:",
                dcc.Input(id='max_leg_length', type='number', min=1, max=20,
                          step=1, value=10),],),
            dbc.Row([
               "Min. Length:",
               dcc.Input(id='min_leg_length', type='number', min=1, max=20,
                         step=1, value=2),]),
            dbc.Row([
               "Max. Slope:",
               dcc.Slider(min=0, max=10, step=1,
                          marks={i: f'{str(i)}' for i in range(0, 11)},
                          value=8, id='max_leg_slope'),]),],
        width=6,),],
        justify="left")],
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
        dcc.Interval(id='check_job_status', interval=2 * 1000, n_intervals=0, disabled=True),
        html.P(id='job_status', children=''),
        dbc.Progress(id="job_status_progress", value=0, color="info", className="mb-3"),]),],
    color="secondary")

app.layout = dbc.Container([
    html.H1("Tour Planner"),
    dbc.Row([
        dbc.Col(tour_config, width=3),
        dbc.Col(cqm_config, width=3),
        dbc.Col(solver_card, width=3),],
        justify="left",),
    dbc.Row([
        graph_card],
        justify="left",),
    dbc.Row([
        dbc.Col([
            dbc.Button("Make CQM", id="btn_update_cqm", color="primary", className="me-1"),
            html.Label('CQM:'),
            dcc.Textarea(id="cqm_print", value='Your CQM',
                style={'width': '50%', 'height': 100}),],),],
        justify="left",),
    dbc.Tooltip("Number of legs for the tour.",
                target="num_legs",),
    dbc.Tooltip("Maximum length for a single leg.",
                target="max_leg_length",),
    dbc.Tooltip("Minimum length for a single leg.",
                target="min_leg_length",),
    dbc.Tooltip("Maximum elevation for a single leg.",
                target="max_leg_slope",),],
    fluid=True, style={"backgroundColor": "black", "color": "#f37820"})

@app.callback(
    Output('max_leg_length', 'value'),
    Output('min_leg_length', 'value'),
    Input('num_legs', 'value'),
    Input('max_leg_length', 'value'),
    Input('min_leg_length', 'value'),
    Input('max_leg_slope', 'value'),)
def update_tour(num_legs, max_leg_length, min_leg_length, max_leg_slope):
    """Build tour

    Args:
        G (networkx Graph)
        k (int):
            Maximum number of communities.

    Returns:
        DiscreteQuadraticModel
    """
    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if "num_legs" == trigger_id:
        tour.num_legs = num_legs
    elif 'max_leg_length' == trigger_id:
        tour.max_length = max_leg_length
        if max_leg_length < tour.min_length:
            tour.min_length = tour.max_length
    elif 'min_leg_length' == trigger_id:
        tour.min_length = min_leg_length
        if min_leg_length > tour.max_length:
            tour.max_length = tour.min_length
    elif 'max_leg_slope' == trigger_id:
        tour.max_elevation = max_leg_slope

    tour.update_config()
    return tour.max_length, tour.min_length

@app.callback(
    Output('test2', 'value'),
    Output('btn_solve_cqm', 'disabled'),
    Output('check_job_status', 'disabled'),
    Input('btn_solve_cqm', 'n_clicks'),)
def submit_cqm(button_solve_cqm):
    """Solve the CQM

    Args:
        G (networkx Graph)
        k (int):
            Maximum number of communities.

    Returns:
        DiscreteQuadraticModel
    """
    solve_button_diabled = False
    timer_disabled = True
    test2_output = "placeholder"
    return_vals = [test2_output, solve_button_diabled, timer_disabled]
    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    # value = input_value if trigger_id == "input-circular" else slider_value
    # changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if "btn_solve_cqm" == trigger_id:
        tour.cqm = build_cqm(tour)
        print(f"solve_cqm button {job_tracker.solver_name} and {tour.cqm}")
        job_tracker.problem_id = upload_cqm(tour.cqm, job_tracker.solver_name)
        #sampleset = sampler.sample_cqm(cqm, time_limit=5)
        #sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
        # data = []
        # for datum in sampleset_feasible.data(fields=['sample', 'energy']):
        #     modes_on = [key.split('_')[0] for key,val in datum.sample.items() if val==1.0]
        #     row = {mode_on: modes_on.count(mode_on) for mode_on in transport.keys()}
        #     row.update({'energy': datum.energy})
        #     data.append(row)
        data = imported_data
        first = sorted({int(key.split('_')[1]): key.split('_')[0] for key,val in data[0].items() if val==1.0}.items())
        return_vals = [str(first), True, False]

    return return_vals[0], return_vals[1], return_vals[2]

@app.callback(
    Output('job_status_progress', 'value'),
    Output('job_status_progress', 'color'),
    Input('job_status', 'children'),)
def get_solution(progress_print):
    """Retrieve solutions from Leap

    Args:
        G (networkx Graph)
        k (int):
            Maximum number of communities.

    Returns:
        DiscreteQuadraticModel
    """
    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if 'job_status' == trigger_id:

        if job_tracker.computation:
            job_tracker.status = job_tracker.computation.remote_status

        print(progress_print)
        progress_bar_val = [int(s) for s in progress_print.split() if s.isdigit()][0]

        if progress_bar_val < 20:
            return progress_bar_val, dash.no_update
        elif progress_bar_val < 40:
            return progress_bar_val, 'warning'
        elif progress_bar_val < 60:
            return progress_bar_val, 'danger'
        else:
            return progress_bar_val, 'success'
    else:
        return dash.no_update, dash.no_update
