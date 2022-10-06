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

from helpers_graphics import *
from helpers_jobs import *
from helpers_layout import *
from formatting import *
from tour_planning import weights_ranges_init, tour_ranges_init
from tour_planning import build_cqm, set_legs, transport
from tool_tips import tool_tips

import dimod
from dwave.cloud.hybrid import Client
from dwave.cloud.api import Problems, exceptions

modes = transport.keys()  # global, but not user modified
num_modes = len(modes)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

client = Client.from_config()
try:
    client.get_solver(supported_problem_types__issubset={"cqm"})
    init_job_status = "READY"
    job_status_color = dict()
except Exception as client_err:
    client = None
    init_job_status = "NO_SOLVER"
    job_status_color = dict(color="red")

# Problem-submission section
############################

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
        html.P(id="job_sm", children="ready", style = dict(display="none")),
        html.P(id="job_id", children="", style = dict(display="none")),
        html.P(id="job_elapsed_time", children=""),
        dbc.Alert(id="alert_cancel", children="", dismissable=True,
            is_open=False,),
        dbc.Button("Cancel Job", id="btn_cancel", color="warning", className="me-1",
            style = dict(display="none")),
        dbc.Row([
                html.Div([
                    html.P("Runtime limit:"),
                    dcc.Input(id="max_runtime", type="number", min=5, max=600,
                        step=5, value=5, style={'marginRight':'10px'}),]),]),]),],
    color="secondary")

# Tab-construction section
##########################
tabs = {}

graphs = {          # also used for display callback
    "Space": "Displays your configured tour, with leg distance as " + \
        "relative length and elevation by color. Will display best found mode of transport.",
    "Time": "Will display best found solution, with leg duration as relative length.",
    "Diversity": "Will display all returned solutions to submitted problems."}
tabs["Graph"] = dbc.Tabs([
    dbc.Tab(dbc.Card([
        dbc.Row([
            dbc.Col([
                html.P(id=f"{key}_intro", children=val, style={"color": "black"}),
                dcc.Graph(id=f"{key.lower()}_graph")], width=12) ])]),
        label=f"{key}",
        tab_id=f"graph_{key.lower()}",
        label_style={"color": "white", "backgroundColor": "black"},)
    for key, val in graphs.items()])

double_tabs = {
    "Problem": "Displays the configured tour: length of each leg, elevation, and "\
        "toll positions.",
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

single_tabs = {
    "CQM": "",
    "Input": "",
    "Transport": out_transport_human(transport)}
for key, val in single_tabs.items():
    tabs[key] = dbc.Card([
        dbc.Row([
            dbc.Col([
                dcc.Textarea(id=f"{key.lower()}_print", value=val,
                    style={"width": "100%"}, rows=20)],)]),])

# Configuration sections
########################

constraint_inputs = {f"weight_{constraint.lower()}": f"{constraint}" for
    constraint in ["Cost", "Time", "Slope"]}      # also used for display callback
constraint_card = [dbc.Row([html.H4("CQM Settings", className="card-title")])]
constraint_card.extend([
    dbc.Row([
       dbc.Col([
            html.Div([
            dbc.Label(f"{val} Weight"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        _dcc_input(key, weights_ranges_init, step=1)],
                            style=dict(display="flex", justifyContent="right")),
                        _dcc_slider(f"{key}_slider", weights_ranges_init),],
                    style={"margin-right": "20px"}),
                dbc.Col([
                    _dcc_radio(key)], style={"margin-left": "30px"})])])])])
    for key, val in constraint_inputs.items()])

tour_titles = ["Set Legs", "Set Budget"]
leg_inputs = {      # also used for callbacks
    "num_legs": "How Many:",
    "max_leg_length": "Longest Leg:",
    "min_leg_length": "Shortest Leg:",
    "max_leg_slope": "Steepest Leg:",}
constraints_inputs = {      # also used for callbacks
    "max_cost": "Highest Cost:",
    "max_time": "Longest Time:"}

leg_row_inputs = [dbc.Row([
    f"{val}",
    dash.html.Br(),
    _dcc_input(key, tour_ranges_init, step=1) if key != "max_leg_slope" else
    _dcc_slider(key, tour_ranges_init, step=1, discrete_slider=True)])
    for key, val in {**leg_inputs, **constraints_inputs}.items()]
tour_config = dbc.Card(
    [dbc.Row([
        html.H4("Tour Settings", className="card-title", style={"textAlign": "left"})]),
     dbc.Row([
        dbc.Col([
            html.B(f"{tour_title}", style={"text-decoration": "underline"},) ])
                for tour_title in tour_titles]),
     dbc.Row([
        dbc.Col(leg_row_inputs[:4], style={"margin-right": "20px"}),
        dbc.Col(leg_row_inputs[4:], style={"margin-left": "20px"}),],),],
    body=True, color="secondary")

# Page-layout section
#####################

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
            dbc.Card(constraint_card, body=True, color="secondary"),
            width=3),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    solver_card])]),],
            width=2)],
        justify="left"),
    dbc.Tabs([
        dbc.Tab(
            tabs[tab], label=tab, tab_id=f"tab_{tab.lower()}",
            label_style={"color": "rgb(6, 236, 220)", "backgroundColor": "black"},)
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
    style={"backgroundColor": "black", "color": "rgb(6, 236, 220)"})

# Callbacks Section
###################

@app.callback(
    Output("solver_modal", "is_open"),
    Input("btn_solve_cqm", "n_clicks"),)
def no_solver(btn_solve_cqm):
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
    [Input("input_print", "value")],
    [State(id, "value") for id in leg_inputs.keys()])
def legs(input_print, num_legs, max_leg_length, min_leg_length, max_leg_slope):
    """Generate the tour legs and write to json & readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "input_print":

        find_changed = [line for line in input_print.split("\n") if "<<--" in line]

        if find_changed and find_changed[0].split(" ")[0] not in leg_inputs.keys():
            return dash.no_update, dash.no_update   # CQM-affecting only inputs
        else:
            legs = set_legs(num_legs, [min_leg_length, max_leg_length], max_leg_slope)
            return tour_to_json(legs), tour_to_display(legs)

@app.callback(
    Output("cqm_print", "value"),
    [Input("input_print", "value")],
    [Input("problem_print_code", "value")],
    [State("max_leg_slope", "value")],
    [State(id, "value") for id in [*constraints_inputs.keys(), *constraint_inputs.keys()]],
    [State(f"{id}_radio", "value") for id in constraint_inputs.keys()])
def cqm(input_print, problem_print_code, max_leg_slope,
    max_cost, max_time, weight_cost, weight_time, weight_slope,
    weight_cost_radio, weight_time_radio, weight_slope_radio):
    """Create the CQM and write to json & readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if any(trigger_id == input for input in ["input_print", "problem_print_code"]):
        legs = tour_from_json(problem_print_code)

        weight_or_none = {}
        for key in constraint_inputs.keys():
            radio_button = f"{key}_radio"
            weight_or_none[key] = None if eval(f"{radio_button} == 'hard'") else eval(key)

        cqm = build_cqm(legs, modes, max_leg_slope, max_cost, max_time,
            weight_or_none["weight_cost"], weight_or_none["weight_time"],
            weight_or_none["weight_slope"])
        return cqm.__str__()

@app.callback(
    [Output("input_print", "value")],
    [Output(id, "value") for id in [*leg_inputs.keys(), *constraint_inputs.keys()]],
    [Output(f"{id}_slider", "value") for id in constraint_inputs.keys()],
    [Input(id, "value") for id in
        [*leg_inputs.keys(), *constraints_inputs.keys(), *constraint_inputs.keys()]],
    [Input(f"{id}_slider", "value") for id in constraint_inputs.keys()],
    [Input(f"{id}_radio", "value") for id in constraint_inputs.keys()],)
def user_inputs(num_legs, max_leg_length, min_leg_length, max_leg_slope,
    max_cost, max_time, weight_cost, weight_time, weight_slope,
    weight_cost_slider,  weight_time_slider, weight_slope_slider,
    weight_cost_radio, weight_time_radio, weight_slope_radio):
    """Handle user inputs and write to readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "max_leg_length" and max_leg_length <= min_leg_length:
        min_leg_length = max_leg_length
    if trigger_id == "min_leg_length" and min_leg_length >= max_leg_length:
        max_leg_length = min_leg_length

    weights = ["cost", "time", "slope"]
    weight_vals = {}
    for weight in weights:
        weight_vals[weight] = eval(f"weight_{weight}")
        if trigger_id == f"weight_{weight}_slider":
            weight_vals[weight] = pow(10, eval(f"weight_{weight}_slider"))
        if trigger_id == f"weight_{weight}":
            weight_vals[weight] = eval(f"weight_{weight}")

    tour_inputs = {**tour_ranges_init, **weights_ranges_init}
    for key in tour_ranges_init.keys():
        tour_inputs[key][2] = eval(key)

    if any(trigger_id == f"{key}_radio" for key in constraint_inputs.keys()):
        for key in constraint_inputs.keys():
            radio_button = f"{key}_radio"
            if eval(f"{radio_button} == 'hard'"):
                tour_inputs[key][2] = None
            else:
                tour_inputs[key][2] = eval(key)

    tour_inputs_names = list(tour_inputs.keys())
    tour_inputs_names.extend([f"{a}_slider" for a in weights_ranges_init.keys()])
    tour_inputs_names.extend([f"{a}_radio" for a in weights_ranges_init.keys()])

    if all(trigger_id != input for input in tour_inputs_names):
        trigger = None
    else:
        trigger = trigger_id.split("_slider")[0] if "slider" in trigger_id else \
            trigger_id.split("_radio")[0]

    return tour_params_to_df(tour_inputs, trigger), \
        num_legs, max_leg_length, min_leg_length, max_leg_slope, \
        weight_vals["cost"], weight_vals["time"], weight_vals["slope"], \
        np.log10(weight_vals["cost"]), np.log10(weight_vals["time"]), np.log10(weight_vals["slope"])

@app.callback(
    [Output(f"{key.lower()}_graph", "figure") for key in graphs.keys()],
    Input("solutions_print_code", "value"),
    Input("problem_print_code", "value"))
def graphics(solutions_print_code, problem_print_code):
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
    fig_time = plot_time(legs, transport, samples)
    fig_diversity = plot_diversity(legs, transport, samples)

    if not fig_time:
        fig_time = fig_diversity = dash.no_update

    return fig_space, fig_time, fig_diversity

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
        status = cancel(client, job_id)
        try:
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
    [Output(id, "disabled") for id in leg_inputs.keys()],
    Input("job_submit_state", "children"),)
def button_control(job_submit_state):
    """Disable tour-effecting user input during job submissions."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id !="job_submit_state":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update, dash.no_update

    if job_status_to_str(job_submit_state) == "SUBMITTED":
        return  dict(), True, True, True, True, True

    if job_status_to_str(job_submit_state) == "PENDING":
        return  dict(), False, True, True, True, True

    elif job_status_to_str(job_submit_state) == "IN_PROGRESS":
        return dict(display="none"), True, dash.no_update, dash.no_update, \
            dash.no_update, dash.no_update

    elif any(job_status_to_str(job_submit_state) == status for status in TERMINATED):
        return dict(display="none"), False, False, False, False, False

    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update, dash.no_update

@app.callback(
    Output("bar_job_status", "value"),
    Output("bar_job_status", "color"),
    Input("job_submit_state", "children"),)
def progress_bar(job_submit_state):
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
    [State(id, "value") for id in constraints_inputs.keys()],
    [State(id, "value") for id in constraint_inputs.keys()],
    [State(f"{id}_radio", "value") for id in constraint_inputs.keys()],
    [State("max_runtime", "value")],)
def job_submit(job_submit_time, problem_print_code, max_leg_slope,
    max_cost, max_time, weight_cost, weight_time, weight_slope,
    weight_cost_radio, weight_time_radio, weight_slope_radio, max_runtime):
    """Submit job and provide job ID."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id =="job_submit_time":

        weight_or_none = {}
        for key in constraint_inputs.keys():
            radio_button = f"{key}_radio"
            weight_or_none[key] = None if eval(f"{radio_button} == 'hard'") else eval(key)

        solver = client.get_solver(supported_problem_types__issubset={"cqm"})
        legs = tour_from_json(problem_print_code)
        cqm = build_cqm(legs, modes, max_leg_slope, max_cost, max_time, \
            weight_or_none["weight_cost"], weight_or_none["weight_time"], \
            weight_or_none["weight_slope"])

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
def solutions(job_submit_state, job_id):
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
def submission_manager(n_clicks, n_intervals, job_id, job_submit_state, job_submit_time):
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

if __name__ == "__main__":
    app.run_server(debug=True)
