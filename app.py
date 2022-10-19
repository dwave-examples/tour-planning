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
import numpy as np
import pandas as pd
import random
import time, datetime

from formatting import *
from helpers_graphics import *
from helpers_jobs import *
from helpers_layout import *
from tour_planning import build_cqm, set_legs, locomotion, tour_budget_boundaries
from tour_planning import (names_locomotion_inputs, names_leg_inputs, names_slope_inputs,
    names_weight_inputs, names_budget_inputs)
from tour_planning import MAX_SOLVER_RUNTIME
from tool_tips import tool_tips

import dimod
from dwave.cloud.hybrid import Client
from dwave.cloud.api import Problems, exceptions

modes = locomotion.keys()  # global, but not user modified
num_modes = len(modes)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

try:
    client = Client.from_config()
    client.get_solver(supported_problem_types__issubset={"cqm"})
    init_job_status = "READY"
    job_status_color = dict()
except Exception as client_err:
    client = None
    init_job_status = "NO_SOLVER"
    job_status_color = dict(color="red")

# Problem-submission section

solver_card = dbc.Card([
    html.H4("Job Submission", className="card-title"),
    dbc.Col([
        dbc.Button("Solve CQM", id="btn_solve_cqm", color="primary", className="me-1"),
        dcc.Interval(id="wd_job", interval=None, n_intervals=0, disabled=True, max_intervals=1),
        dbc.Progress(id="bar_job_status", value=job_bar[init_job_status][0],
            color=job_bar[init_job_status][1], className="mb-3"),
        html.P(id="job_submit_state", children=job_status_to_display(init_job_status),
            style=job_status_color),
        html.P(id="job_submit_time", children="", style = dict(display="none")),
        html.P(id="job_id", children="", style = dict(display="none")),
        html.P(id="job_elapsed_time", children=""),
        dbc.Alert(id="alert_cancel", children="", dismissable=True,
            is_open=False,),
        dbc.Button("Cancel Job", id="btn_cancel", color="warning", className="me-1",
            style = dict(display="none")),
        dbc.Row([
                html.Div([
                    html.P("Runtime limit:"),
                    dcc.Input(id="max_runtime", type="number", min=5, max=MAX_SOLVER_RUNTIME,
                        step=5, value=5, style={'marginRight':'10px'}),]),]),]),],
    color="secondary")

# Tab-construction section

tabs = {}

graphs = ["Space", "Time", "Feasibility"] # also used for graph() display callback
tabs["Graph"] = dbc.Tabs([
    dbc.Tab(dbc.Card([
        dbc.Row([
            dbc.Col([
                dcc.Graph(id=f"{graph.lower()}_graph")], width=12) ])]),
        label=f"{graph}",
        id=f"graph_{graph.lower()}",
        label_style={"color": "white", "backgroundColor": "black"},)
    for graph in graphs])

double_tabs = {
    "Problem": "Displays the configured tour: length of each leg, elevation, and "\
        "toll positions.", # Unused text kept in case of future changes
    "Solutions": "Displays returned solutions to submitted problems."}
readers = ["Human", "Code"]
viewer_tabs = {}
for key, val in double_tabs.items():
    tabs[key] = dbc.Tabs([
        dbc.Tab(dbc.Card([
            dbc.Row([
                dbc.Col([
                    dcc.Textarea(id=f"{key.lower()}_print_{reader.lower()}", value=val,
                        style={"width": "100%"}, rows=20)])]),]),
            label=f"{reader} Readable",
            tab_id=f"tab_{key}_print_{reader.lower()}",
            label_style={"color": "white", "backgroundColor": "black"},)
    for reader in readers])

tabs["CQM"] = dbc.Card([
    dbc.Row([
        dbc.Col([
            dcc.Textarea(id=f"cqm_print", value="",
                style={"width": "100%"}, rows=20)],)]),])

locomotion_columns = ["Mode", "Speed", "Cost", "Exercise"]
tabs["Locomotion"] = dbc.Card([
    dbc.Row([
        dbc.Col([
            dcc.Textarea(id=f"locomotion_print", value="",
                style={"width": "100%"}, rows=5)],)]),
    dbc.Row([html.P("Locomotion Settings")]),
    dbc.Row([
        dbc.Col([html.P(f"{col}")], width=1) for col in locomotion_columns]),
    *[dbc.Row([
        dbc.Col([html.P(f"{row}")], width=1),
        *[dbc.Col([_dcc_input(f"{name}")], width=1) for name in
            names_locomotion_inputs if row in name]]) for row in locomotion.keys()]],
        style={"color": "rgb(3, 184, 255)", "backgroundColor": "black"})

# CQM configuration sections

weights_card = [dbc.Row([html.H4("Constraint Settings", className="card-title")],
    id="constraint_settings_row")]
weights_card.extend([
    dbc.Row([
       dbc.Col([
            html.Div([
            dbc.Label(f"{val} Weight"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        _dcc_input(key, step=1)],
                            style=dict(display="flex", justifyContent="right")),
                        _dcc_radio(key, "penalty")],
                    style={"margin-right": "20px"}),
                dbc.Col([
                    _dcc_radio(key, "hardsoft")], style={"margin-left": "30px"})])])])])
    for key, val in zip(names_weight_inputs, ["Cost", "Time", "Slope"])])

tour_titles = ["Set Legs", "Set Budget", "Set Exercise Limits"]
field_titles = ["How Many:", "Longest Leg:", "Shortest Leg:",
    "Highest Cost:", "Longest Time:", "Steepest Leg:"]

leg_fields = [dbc.Row([
    f"{val}",
    dash.html.Br(),
    _dcc_input(key, step=1) if key != "max_leg_slope" else
    _dcc_slider(key, step=1)])
    for key, val in zip(names_leg_inputs + names_budget_inputs + names_slope_inputs, field_titles)]
tour_config = dbc.Card(
    [dbc.Row([
        html.H4("Tour Settings", className="card-title", style={"textAlign": "left"})],
        id="tour_settings_row"),
     dbc.Row([
        dbc.Col([
            html.B(f"{tour_title}", style={"text-decoration": "underline"},) ])
                for tour_title in tour_titles[:2]]),
     dbc.Row([
        dbc.Col(leg_fields[:3], style={"margin-right": "20px"}),
        dbc.Col(leg_fields[3:5], style={"margin-left": "20px"}),]),

     dbc.Row([
        dbc.Col([
            html.Br(),
            html.B(f"{tour_title}", style={"text-decoration": "underline"},) ])
                for tour_title in tour_titles[2:]]),
     dbc.Row([
        dbc.Col(leg_fields[5], style={"margin-right": "20px"}),
        dbc.Col()],),
     html.P(id="changed_input", children="", style = dict(display="none")),],
    body=True, color="secondary")

# Page-layout section

layout = [
    dbc.Row([
        dbc.Col([
            html.H1("Tour Planner", style={"textAlign": "left"})], width=10),
        dbc.Col([
            html.Img(src="assets/ocean.png", height="50px",
                style={"textAlign": "right"})], width=2)]),
    dbc.Row([
        dbc.Col(
            tour_config, width=4),
        dbc.Col(
            dbc.Card(weights_card, body=True, color="secondary"),
            width=3),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    solver_card])]),],
            width=2),
        dbc.Col([], width=1),
        dbc.Col([
            dbc.Row([
                html.P(" ")]),
            dbc.Row([
                html.P("Hover your mouse over any field for descriptions.",
                    style={"color": "white"})]),],
            width=1)],
        justify="left"),
    dbc.Tabs([
        dbc.Tab(
            tabs[tab], label=tab, tab_id=f"tab_{tab.lower()}",
            label_style={"color": "rgb(3, 184, 255)", "backgroundColor": "black"},
            id=f"tab_for_{tab}")
        for tab in tabs.keys()],
        id="tabs", active_tab="tab_graph")]

tips = [dbc.Tooltip(
            message, target=target)
            for target, message in tool_tips.items()]
layout.extend(tips)

modal = [html.Div([
    dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle("Leap Hybrid CQM Solver Inaccessible")),
        dbc.ModalBody(no_solver_msg),], id="solver_modal", size="sm")])]
layout.extend(modal)

app.layout = dbc.Container(
    layout, fluid=True,
    style={"backgroundColor": "black", "color": "rgb(3, 184, 255)"})

server = app.server
app.config["suppress_callback_exceptions"] = True

# Callbacks Section

def _weight_or_none(
    weight_cost, weight_time, weight_slope,
    weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft):
    """Helper function for `build_cqm()`, which is used twice."""

    weights = {
        "cost": None if weight_cost_hardsoft == "hard" \
            else weight_cost,
        "time": None if weight_time_hardsoft == "hard" \
            else weight_time,
        "slope": None if weight_slope_hardsoft == "hard" \
            else weight_slope}

    return weights

@app.callback(
    Output("solver_modal", "is_open"),
    Input("btn_solve_cqm", "n_clicks"),)
def alert_no_solver(btn_solve_cqm):
    """Notify if no Leap hybrid CQM solver is accessible."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "btn_solve_cqm":
        if not client:
            return True

    return False

@app.callback(
    [Output("problem_print_code", "value")],
    [Output("problem_print_human", "value")],
    [Input("changed_input", "children")],
    [State(id, "value") for id in names_leg_inputs])
def update_legs(changed_input, num_legs, max_leg_length, min_leg_length):
    """Generate the tour legs and write to json & readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    # This ``trigger_id and not changed_input`` enables the chain of
    # callbacks at startup for initial displays.
    if trigger_id and not changed_input or any(changed_input == key for key in
        names_leg_inputs):

        legs = set_legs(num_legs, min_leg_length, max_leg_length)
        return tour_to_json(legs), tour_to_display(legs)

    else:       # Other user inputs regenerate the CQM but not the legs

        return dash.no_update, dash.no_update

@app.callback(
    Output("locomotion_print", "value"),
    [Input("cqm_print", "value")],
    [State("problem_print_code", "value")],
    [State(id, "value") for id in names_locomotion_inputs],)
def display_locomotion(cqm_print, problem_print_code,
    walk_speed, walk_cost, walk_exercise,
    cycle_speed, cycle_cost, cycle_exercise,
    bus_speed, bus_cost, bus_exercise,
    drive_speed, drive_cost, drive_exercise):
    """Update the locomotion display print."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "cqm_print":

        locomotion_vals = {"walk": [walk_speed, walk_cost, walk_exercise],
    "cycle": [cycle_speed, cycle_cost, cycle_exercise],
    "bus": [bus_speed, bus_cost, bus_exercise],
    "drive": [drive_speed, drive_cost, drive_exercise]}

        legs = tour_from_json(problem_print_code)
        boundaries = tour_budget_boundaries(legs, locomotion_vals)

        return locomotion_to_display(boundaries)

@app.callback(
    Output("cqm_print", "value"),
    [Input("changed_input", "children")],
    [Input("problem_print_code", "value")],
    [State("max_leg_slope", "value")],
    [State(id, "value") for id in names_budget_inputs + names_weight_inputs],
    [State(f"{id}_hardsoft", "value") for id in names_weight_inputs],
    [State(f"{id}_penalty", "value") for id in names_weight_inputs],
    [State(id, "value") for id in names_locomotion_inputs])
def generate_cqm(changed_input, problem_print_code, max_leg_slope,
    max_cost, max_time, weight_cost, weight_time, weight_slope,
    weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft,
    weight_cost_penalty, weight_time_penalty, weight_slope_penalty,
    walk_speed, walk_cost, walk_exercise,
    cycle_speed, cycle_cost, cycle_exercise,
    bus_speed, bus_cost, bus_exercise,
    drive_speed, drive_cost, drive_exercise):
    """Create the CQM and write to json & readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    # Even when `changed_input` is generated by inputs in names_leg_inputs, no need
    # to wait for `problem_print_code`: update_legs() callback completes
    # first, even if it is deliberately slowed.
    if trigger_id == "changed_input" or trigger_id == "problem_print_code":
        legs = tour_from_json(problem_print_code)

        penalties = {
            "cost": weight_cost_penalty,
            "time": weight_time_penalty,
            "slope": weight_slope_penalty}

        weights = _weight_or_none(weight_cost, weight_time, weight_slope,
            weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft)

        locomotion_vals = {"walk": [walk_speed, walk_cost, walk_exercise],
            "cycle": [cycle_speed, cycle_cost, cycle_exercise],
            "bus": [bus_speed, bus_cost, bus_exercise],
            "drive": [drive_speed, drive_cost, drive_exercise]}

        cqm = build_cqm(legs, modes, max_leg_slope, max_cost, max_time,
            weights, penalties, locomotion_vals)

        return cqm.__str__()

    return dash.no_update

@app.callback(
    [Output("changed_input", "children")],
    [Output("max_leg_length", "value")],
    [Output("min_leg_length", "value")],
    [Input(id, "value") for id in
        names_leg_inputs + names_slope_inputs + names_budget_inputs + names_weight_inputs],
    [Input(f"{id}_penalty", "value") for id in names_weight_inputs],
    [Input(f"{id}_hardsoft", "value") for id in names_weight_inputs],
    [Input(id, "value") for id in names_locomotion_inputs],)
def check_user_inputs(num_legs, max_leg_length, min_leg_length, max_leg_slope,
    max_cost, max_time, weight_cost, weight_time, weight_slope,
    weight_cost_penalty,  weight_time_penalty, weight_slope_penalty,
    weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft,
    walk_speed, walk_cost, walk_exercise,
    cycle_speed, cycle_cost, cycle_exercise,
    bus_speed, bus_cost, bus_exercise,
    drive_speed, drive_cost, drive_exercise):
    """Handle user inputs and write to readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "max_leg_length" and max_leg_length <= min_leg_length:
        min_leg_length = max_leg_length
    if trigger_id == "min_leg_length" and min_leg_length >= max_leg_length:
        max_leg_length = min_leg_length

    return trigger_id, max_leg_length, min_leg_length

@app.callback(
    [Output(f"{graph.lower()}_graph", "figure") for graph in graphs],
    Input("solutions_print_code", "value"),
    Input("problem_print_code", "value"))
def display_graphics(solutions_print_code, problem_print_code):
    """Generate graphics for legs and samples."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    legs = tour_from_json(problem_print_code)

    samples = None
    if trigger_id == "solutions_print_code":
        samples = sampleset_from_json(solutions_print_code)
        if not isinstance(samples, dict):
            samples = None

    fig_space = plot_space(legs, samples)
    fig_time = plot_time(legs, locomotion, samples)
    fig_feasiblity = plot_feasiblity(legs, locomotion, samples)

    if not fig_time:
        fig_time = fig_feasiblity = dash.no_update

    return fig_space, fig_time, fig_feasiblity

@app.callback(
    Output("alert_cancel", "children"),
    Output("alert_cancel", "is_open"),
    Input("btn_cancel", "n_clicks"),
    State("job_id", "children"),)
def cancel_submission(btn_cancel, job_id):
    """Try to cancel the current job submission."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id !="btn_cancel":
        return dash.no_update, dash.no_update
    else:
        try:
            status = cancel(client, job_id)
            if status.status.name == "CANCELLED":
                alert = f"Cancelled job {job_id}"
            else:
                alert = f"Could not cancel job: {status}"
        except Exception as err:
            alert = f"Could not cancel job: {err}"

        return alert, True

@app.callback(
    Output("btn_cancel", component_property="style"),
    Output("btn_cancel", "disabled"),
    [Output(id, "disabled") for id in names_leg_inputs],
    Input("job_submit_state", "children"),)
def disable_buttons(job_submit_state):
    """Disable tour-effecting user input during job submissions."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id !="job_submit_state":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update

    if job_status_to_str(job_submit_state) == "SUBMITTED":
        return  dict(), True, True, True, True

    if job_status_to_str(job_submit_state) == "PENDING":
        return  dict(), False, True, True, True

    elif job_status_to_str(job_submit_state) == "IN_PROGRESS":
        return dict(display="none"), True, dash.no_update, dash.no_update, \
            dash.no_update

    elif any(job_status_to_str(job_submit_state) == status for status in TERMINATED):
        return dict(display="none"), False, False, False, False

    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update

@app.callback(
    Output("bar_job_status", "value"),
    Output("bar_job_status", "color"),
    Input("job_submit_state", "children"),)
def set_progress_bar(job_submit_state):
    """Update progress bar for job submissions."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id != "job_submit_state":
        return job_bar["READY"][0], job_bar["READY"][1]
    else:
        state = job_status_to_str(job_submit_state)
        return job_bar[state][0], job_bar[state][1]

@app.callback(
    Output("job_id", "children"),
    [Input("job_submit_time", "children")],
    [State("problem_print_code", "value")],
    [State("max_leg_slope", "value")],
    [State(id, "value") for id in names_budget_inputs],
    [State(id, "value") for id in names_weight_inputs],
    [State(f"{id}_hardsoft", "value") for id in names_weight_inputs],
    [State(f"{id}_penalty", "value") for id in names_weight_inputs],
    [State(id, "value") for id in names_locomotion_inputs],
    [State("max_runtime", "value")],)
def submit_job(job_submit_time, problem_print_code, max_leg_slope,
    max_cost, max_time, weight_cost, weight_time, weight_slope,
    weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft,
    weight_cost_penalty, weight_time_penalty, weight_slope_penalty,
    walk_speed, walk_cost, walk_exercise,
    cycle_speed, cycle_cost, cycle_exercise,
    bus_speed, bus_cost, bus_exercise,
    drive_speed, drive_cost, drive_exercise,
    max_runtime):
    """Submit job and provide job ID."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id =="job_submit_time":

        solver = client.get_solver(supported_problem_types__issubset={"cqm"})

        penalties = {
            "cost": weight_cost_penalty,
            "time": weight_time_penalty,
            "slope": weight_slope_penalty}

        weights = _weight_or_none(weight_cost, weight_time, weight_slope,
            weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft)

        legs = tour_from_json(problem_print_code)

        locomotion_vals = {"walk": [walk_speed, walk_cost, walk_exercise],
            "cycle": [cycle_speed, cycle_cost, cycle_exercise],
            "bus": [bus_speed, bus_cost, bus_exercise],
            "drive": [drive_speed, drive_cost, drive_exercise]}

        cqm = build_cqm(legs, modes, max_leg_slope, max_cost, max_time,
            weights, penalties, locomotion_vals)

        problem_data_id = solver.upload_cqm(cqm).result()
        computation = solver.sample_cqm(problem_data_id,
                    label=f"Examples - Tour Planning, submitted: {job_submit_time}",
                    time_limit=max_runtime)

        return computation.wait_id()

    return dash.no_update
#
@app.callback(
    Output("solutions_print_code", "value"),
    Output("solutions_print_human", "value"),
    Input("job_submit_state", "children"),
    State("job_id", "children"),)
def display_solutions(job_submit_state, job_id):
    """Update solutions and write to json & readable text."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id != "job_submit_state":
        return dash.no_update, dash.no_update

    if any(job_status_to_str(job_submit_state) == status for status in TERMINATED):
        if job_status_to_str(job_submit_state) == "COMPLETED":
            sampleset = client.retrieve_answer(job_id).sampleset
            return sampleset_to_json(sampleset), solutions_to_display(sampleset)
        else:
            return "No solutions for last submission", "No solutions for last submission"
    else: # Other submission states like PENDING
        return dash.no_update, dash.no_update

@app.callback(
    Output("btn_solve_cqm", "disabled"),
    Output("wd_job", "disabled"),
    Output("wd_job", "interval"),
    Output("wd_job", "n_intervals"),
    Output("job_submit_state", "children"),
    Output("job_submit_time", "children"),
    Output("job_elapsed_time", "children"),
    Input("btn_solve_cqm", "n_clicks"),
    Input("wd_job", "n_intervals"),
    State("job_id", "children"),
    State("job_submit_state", "children"),
    State("job_submit_time", "children"),)
def manage_submission(n_clicks, n_intervals, job_id, job_submit_state, job_submit_time):
    """Manage job submission."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if not any(trigger_id == input for input in ["btn_solve_cqm", "wd_job"]):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update, dash.no_update, dash.no_update

    if trigger_id == "btn_solve_cqm":

        submit_time = datetime.datetime.now().strftime("%c")
        disable_btn = True
        disable_watchdog = False

        return disable_btn, disable_watchdog, 0.2*1000, 0, \
            job_status_to_display("SUBMITTED"), submit_time, f"Elapsed: 0 sec."

    if any(job_status_to_str(job_submit_state) == status for status in
        ["SUBMITTED", *RUNNING]):

        job_submit_state = get_status(client, job_id, job_submit_time)
        if not job_submit_state:
            job_submit_state = "SUBMITTED"
            wd_time = 0.2*1000
        else:
            wd_time = 1*1000

        elapsed_time = elapsed(job_submit_time)

        return True, False, wd_time, 0, \
            job_status_to_display(job_submit_state), dash.no_update, \
            f"Elapsed: {elapsed_time} sec."

    if any(job_status_to_str(job_submit_state) == status for status in TERMINATED):

        elapsed_time = elapsed(job_submit_time)
        disable_btn = False
        disable_watchdog = True

        return disable_btn, disable_watchdog, 0.1*1000, 0, \
            dash.no_update, dash.no_update, f"Elapsed: {elapsed_time} sec."

    else:   # Exception state: should only ever happen in testing

        return False, True, 0, 0, job_status_to_display("ERROR"), dash.no_update, \
            "Please restart"

if __name__ == "__main__":
    app.run_server(debug=True)
