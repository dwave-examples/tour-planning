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

from json import JSONDecodeError
import time, datetime

from dwave.cloud.hybrid import Client
from dwave.cloud.api import Problems, exceptions

from helpers import formatting
from helpers import graphics
from helpers import jobs
from helpers import layout
from helpers.layout import (description_space_plot, description_time_plot,
    description_feasibility_plot, description_problem_print, description_solutions_print,
    description_cqm_print, description_locomotion_print)
from helpers.tool_tips import tool_tips
from tour_planning import (build_cqm, set_legs, tour_budget_boundaries,
    names_locomotion_inputs, names_leg_inputs, names_slope_inputs,
    names_weight_inputs, names_budget_inputs, names_all_modes)
from tour_planning import MAX_SOLVER_RUNTIME

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

try:
    client = Client.from_config()
    client.get_solver(supported_problem_types__issuperset={"cqm"})
    init_job_status = "READY"
    job_status_color = dict()
except Exception as client_err:
    client = None
    init_job_status = "NO_SOLVER"
    job_status_color = dict(color="red")

# Problem-submission section

solver_card = dbc.Card([
    html.H4("Job Submission", className="card-title",
        style={"color":"rgb(243, 120, 32)"}),
    dbc.Col([
        dbc.Button("Solve CQM", id="btn_solve_cqm", color="primary", className="me-1",
            style={"marginBottom":"5px"}),
        dcc.Interval(id="wd_job", interval=None, n_intervals=0, disabled=True, max_intervals=1),
        dbc.Progress(id="bar_job_status", value=jobs.job_bar[init_job_status][0],
            color=jobs.job_bar[init_job_status][1], className="mb-3",
            style={"width": "60%"}),
        html.P(id="job_submit_state", children=formatting.job_status_to_display(init_job_status),
            style={"color": "white", "fontSize": 12}),
        html.P(id="job_submit_time", children="", style = dict(display="none")),
        html.P(id="job_id", children="", style = dict(display="none")),
        html.P(id="job_elapsed_time", children="",
            style={"color": "white", "fontSize": 12}),
        dbc.Alert(id="alert_cancel", children="", dismissable=True,
            is_open=False,),
        dbc.Button("Cancel Job", id="btn_cancel", color="warning", className="me-1",
            style = dict(display="none")),
        html.Hr(),
        html.P("Runtime limit:",
            style={"color": "white", "fontSize": 12, "marginBottom": 5}),
        dcc.Input(id="max_runtime", type="number", min=5, max=MAX_SOLVER_RUNTIME,
            step=5, value=5,
            style={"max-width": "30%"})],
        width=12)],
    color="dark", body=True)

# Tab-construction section

tabs = {}

graph_tabs = [dbc.Tab(
    dbc.Card([
        dbc.Row([
            dbc.Col([
                dcc.Graph(id=f"{graph.lower()}_graph")],
                width=12)]),
        dbc.Row([
            dbc.Col([
                html.P(globals()[f"description_{graph.lower()}_plot"],
                    style={"color": "white", "fontSize": 12})],
                width=10)],
            align="start")],
        color="dark"),
    label=f"{graph}",
    id=f"graph_{graph.lower()}",
    label_style={"color": "white", "backgroundColor": "black"},)
    for graph in ["Space", "Time", "Feasibility"]]
tabs["Graph"] = dbc.Tabs(graph_tabs)

double_tabs = {
    "Problem": "Displays the configured tour: length of each leg, elevation, and "\
        "toll positions.", # Unused text kept in case of future changes
    "Solutions": "Displays returned solutions to submitted problems."}
readers = ["Human", "Code"]
viewer_tabs = {}
for key, val in double_tabs.items():
    tabs[key] = dbc.Tabs([
        dbc.Tab(
            dbc.Card([
                dbc.Row([
                    dbc.Col([
                        dcc.Textarea(id=f"{key.lower()}_print_{reader.lower()}", value=val,
                            style={"width": "100%"}, rows=10)],
                            width=12)]),
                dbc.Row([
                    dbc.Col([
                        html.P(globals()[f"description_{key.lower()}_print"],
                            style={"color": "white", "fontSize": 12})],
                        width=10)],
                    align="start"),],
                color="dark"),
            label=f"{reader} Readable",
            tab_id=f"tab_{key}_print_{reader.lower()}",
            label_style={"color": "white", "backgroundColor": "black"},)
        for reader in readers])

tabs["CQM"] = dbc.Card([
    dbc.Row([
        dbc.Col([
            dcc.Textarea(id=f"cqm_print", value="",
                style={"width": "100%"}, rows=15)],),
    dbc.Row([
        dbc.Col([
            html.P(description_cqm_print,
                style={"color": "white", "fontSize": 12})],
            width=10)],
        align="start")]),],
    color="dark")

locomotion_columns = ["Mode", "Speed", "Cost", "Exercise", "Use"]
tabs["Locomotion"] = dbc.Card([
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    html.P(f"{col}")],
                    width=2) for col in locomotion_columns]),
            *[dbc.Row([
                dbc.Col([
                    html.P(f"{row}:",
                        style={"color": "white", "fontSize": 12})],
                    width=2),
                *[dbc.Col(
                    [layout._dcc_input(f"{name}")],
                    width=2)
                    for name in names_locomotion_inputs if row in name],
                dbc.Col(
                    [dcc.Checklist([
                        {"label": html.Div([""],),
                         "value": True,},], value=[True], id=f"{row}_use"),],
                        width=2),])
                for row in names_all_modes]],
            width=6),
        dbc.Col([
            dcc.Textarea(id=f"locomotion_print", value="",
                style={"width": "100%"}, rows=5)],
            width=5),
    html.P(id="locomotion_state", children="", style = dict(display="none"))]),
    dbc.Row([
        dbc.Col([
            html.P(description_locomotion_print,
                style={"color": "white", "fontSize": 12})],
            width=10)],
        align="start")],
    color="dark")

# CQM configuration sections

weights_card = [
    dbc.Row([
        html.H4("Constraint Settings", className="card-title",
            style={"color": "rgb(243, 120, 32)"}),
        html.P(id="weights_state", children="",
            style = dict(display="none"))],
        id="constraint_settings_row")]

for key, val in zip(names_weight_inputs, ["Cost", "Time", "Slope"]):
    weights_card.extend([
        dbc.Row([
            dbc.Col([
                html.P(f"{val}",
                    style={"marginBottom": 10})],
                width=12)]),
        dbc.Row([
            dbc.Col([
                html.P(f"{key}",
                    style={"color": "white", "fontSize": 12, "marginBottom": 5})],
                width=4)
                for key in ["Constraint:", "Weight:", "Penalty:"]]),
        dbc.Row([
            dbc.Col([
                layout._dcc_radio(key, "hardsoft")],
                width=4),
            dbc.Col([
                layout._dcc_input(key, step=1),],
                width=4),
            dbc.Col([
                layout._dcc_radio(key, "penalty")],
                width=4)]),
        dbc.Row([
            dbc.Col([
                html.Hr()])])
            if val != "Slope" else  html.P(style={"marginBottom": 0})])

tour_config = dbc.Card([
    dbc.Row([
        dbc.Col([
            html.H4("Tour Settings", className="card-title",
                style={"color": "rgb(243, 120, 32)"})])],
        id="tour_settings_row"),
    dbc.Row([
        dbc.Col([
            html.P(f"{title}",
                style={"marginBottom": 0}) ],
            width=6)
        for title in ["Legs", "Budget"]]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    html.P(f"{label}",
                        style={"color": "white", "fontSize": 12,
                            "marginBottom": 5, "marginTop": 10}),
                    layout._dcc_input(input_name, step=1)],
                    width=12)
                for label, input_name in
                zip(["How Many:", "Longest:", "Shortest:"], names_leg_inputs)])],
            width=6),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    html.P(f"{label}",
                        style={"color": "white", "fontSize": 12,
                            "marginBottom": 5, "marginTop": 10}),
                    layout._dcc_input(input_name, step=1)],
                    width=12)
                for label, input_name in
                zip(["Cost:", "Time:"], names_budget_inputs)]),],
            width=6)]),
    dbc.Row([dbc.Col([html.Hr()], style={"marginBottom": 5})]),
    dbc.Row([
        dbc.Col([
            html.P(f"{title}",
                style={"marginBottom": 10})],
            width=6)
        for title in ["Exercise Limits", "Tollbooths"]]),
    dbc.Row([
        dbc.Col([
            html.P("Steepest Leg:",
                style={"color": "white", "fontSize": 12, "marginBottom": 5}),
            html.Div([
                layout._dcc_slider(names_slope_inputs[0], step=1)],
                    style={"marginLeft": -20})],
            width=6),
        dbc.Col([
            html.P("Random tollbooths:",
                style={"color": "white", "fontSize": 12, "marginBottom": 5}),
            layout._dcc_radio("tollbooths", "active")],
            width=6),
        html.P(id="changed_input", children="", style = dict(display="none")),],)],
    body=True, color="dark")

# Page-layout section

app_layout = [
    dbc.Row([
        dbc.Col(
            tour_config,
            width=4),
        dbc.Col(
            dbc.Card(weights_card, body=True, color="dark"),
            width=4),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    solver_card])]),
            dbc.Row([
                dbc.Col([
                    html.P("Tooltips",
                        style={"marginTop": 30}),
                    html.P("Hover over fields for descriptions:",
                        style={"color": "white", "fontSize": 12, "marginBottom": 5}),
                    layout._dcc_radio("tooltips", "active")])]),],
            width=3),],
        justify="left"),
    dbc.Tabs([
        dbc.Tab(
            tabs[tab], label=tab, tab_id=f"tab_{tab.lower()}",
            label_style={"color": "rgb(3, 184, 255)", "backgroundColor": "black"},
            id=f"tab_for_{tab}")
        for tab in tabs.keys()],
        id="tabs", active_tab="tab_graph")]

tips = [dbc.Tooltip(
            message, target=target, id=f"tooltip_{target}", style = dict())
            for target, message in tool_tips.items()]
app_layout.extend(tips)

modal_solver = layout._dbc_modal("modal_solver")
app_layout.extend(modal_solver)
modal_usemodes = layout._dbc_modal("modal_usemodes")
app_layout.extend(modal_usemodes)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Tour Planner", style={"textAlign": "left", "color": "white"})],
            width=9),
        dbc.Col([
            html.Img(src="assets/dwave_logo.png", height="25px",
                style={"textAlign": "left"})],
            width=3)]),
    dbc.Container(app_layout, fluid=True,
        style={"backgroundColor": "black", "color": "rgb(3, 184, 255)",
            "paddingLeft": 10, "paddingRight": 10})],
    style={"backgroundColor": "black",
        "background-image": "url('assets/electric_squids.png')",
        "background-size": "cover",
        "paddingLeft": 100, "paddingRight": 100,
        "paddingTop": 25, "paddingBottom": 50}, fluid=True)

server = app.server
app.config["suppress_callback_exceptions"] = True

# Callbacks Section

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

def radio_disable(disable):
    return [
        {"label": "Linear", "value": "linear", "disabled": disable},
        {"label": "Quadratic", "value": "quadratic", "disabled": disable}]

radio_label_style = {"color": "white", "font-size": 12, "display": "flex"}

@app.callback(
    [Output(id, "disabled") for id in names_weight_inputs],
    [Output(f"{id}_penalty", component_property="options") for id in names_weight_inputs],
    [Output(f"{id}_penalty", component_property="labelStyle") for id in names_weight_inputs],
    [Input(f"{id}_hardsoft", "value") for id in names_weight_inputs],)
def disable_weights(weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft):
    """Disable weight inputs for hard constraints."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if any(trigger_id == f"{weight}_hardsoft" for weight in names_weight_inputs):

        disable = {"cost": False, "time": False, "slope": False}
        for weight in names_weight_inputs:
            if vars()[f"{weight}_hardsoft"] == "hard":
                disable[weight.split("_")[1]] = True
        return disable["cost"], disable["time"], disable["slope"], \
            radio_disable(disable["cost"]), \
            radio_disable(disable["time"]), \
            radio_disable(disable["slope"]), \
            radio_label_style, radio_label_style, radio_label_style

    return dash.no_update, dash.no_update, dash.no_update, \
           dash.no_update, dash.no_update, dash.no_update, \
            dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output(f"tooltip_{target}", component_property="style") for target in tool_tips.keys()],
    Input("tooltips_active", "value"),)
def activate_tooltips(tooltips_active):
    """Activate or hide tooltips."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "tooltips_active":
        if tooltips_active == "off":
            return \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none"), dict(display="none"), dict(display="none"), dict(display="none"), \
dict(display="none")

    return dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), \
dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), \
dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), \
dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), \
dict(), dict(), dict(), dict(), dict(), dict(), dict(), dict(), \
dict()

@app.callback(
    [Output("problem_print_code", "value")],
    [Output("problem_print_human", "value")],
    [Input("changed_input", "children")],
    [State(id, "value") for id in names_leg_inputs],
    [State("tollbooths_active", "value")],)
def update_legs(changed_input, num_legs, max_leg_length, min_leg_length,
    tollbooths_active):
    """Generate the tour legs and write to json & readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    # This ``trigger_id and not changed_input`` enables the chain of
    # callbacks at startup for initial displays.
    if trigger_id and not changed_input or any(changed_input == key for key in
        names_leg_inputs):

        legs = set_legs(num_legs, min_leg_length, max_leg_length, tollbooths_active)
        return formatting.tour_to_json(legs), formatting.tour_to_display(legs)

    else:       # Other user inputs regenerate the CQM but not the legs

        return dash.no_update, dash.no_update

@app.callback(
    Output("locomotion_print", "value"),
    [Input("cqm_print", "value")],
    [State("problem_print_code", "value")],
    [State("locomotion_state", "children")],)
def display_locomotion(cqm_print, problem_print_code, locomotion_state):
    """Update the locomotion display print."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "cqm_print":

        locomotion_vals = formatting.state_from_json(locomotion_state)
        legs = formatting.tour_from_json(problem_print_code)
        boundaries = tour_budget_boundaries(legs, locomotion_vals)

        return formatting.locomotion_to_display(boundaries)

@app.callback(
    Output("cqm_print", "value"),
    [Input("changed_input", "children")],
    [Input("problem_print_code", "value")],
    [State("max_leg_slope", "value")],
    [State(id, "value") for id in names_budget_inputs],
    [State("weights_state", "children")],
    [State("locomotion_state", "children")])
def generate_cqm(changed_input, problem_print_code, max_leg_slope,
    max_cost, max_time, weights_state, locomotion_state,):
    """Create the CQM and write to json & readable text."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    # Even when `changed_input` is generated by inputs in names_leg_inputs, no need
    # to wait for `problem_print_code`: update_legs() callback completes
    # first, even if it is deliberately slowed.
    if trigger_id == "changed_input" or trigger_id == "problem_print_code":
        legs = formatting.tour_from_json(problem_print_code)

        weight_vals = formatting.state_from_json(weights_state)
        locomotion_vals = formatting.state_from_json(locomotion_state)

        cqm = build_cqm(legs, max_leg_slope, max_cost, max_time,
            weight_vals, locomotion_vals)

        return formatting.cqm_to_display(cqm)

    return dash.no_update

@app.callback(
    [Output("changed_input", "children")],
    [Output("max_leg_length", "value")],
    [Output("min_leg_length", "value")],
    [Output(f"{id}_use", "value") for id in names_all_modes],
    [Output("usemodes_modal", "is_open")],
    [Output("locomotion_state", "children")],
    [Output("weights_state", "children")],
    [Input(id, "value") for id in
        names_leg_inputs + names_slope_inputs + names_budget_inputs + names_weight_inputs],
    [Input(f"{id}_penalty", "value") for id in names_weight_inputs],
    [Input(f"{id}_hardsoft", "value") for id in names_weight_inputs],
    [Input(id, "value") for id in names_locomotion_inputs],
    [Input(f"{id}_use", "value") for id in names_all_modes],)
def check_user_inputs(num_legs, max_leg_length, min_leg_length, max_leg_slope,
    max_cost, max_time, weight_cost, weight_time, weight_slope,
    weight_cost_penalty,  weight_time_penalty, weight_slope_penalty,
    weight_cost_hardsoft, weight_time_hardsoft, weight_slope_hardsoft,
    walk_speed, walk_cost, walk_exercise,
    cycle_speed, cycle_cost, cycle_exercise,
    bus_speed, bus_cost, bus_exercise,
    drive_speed, drive_cost, drive_exercise,
    walk_use, cycle_use, bus_use, drive_use):
    """Handle user inputs, identify changed input to other callbacks, save states."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "max_leg_length" and max_leg_length <= min_leg_length:
        min_leg_length = max_leg_length
    if trigger_id == "min_leg_length" and min_leg_length >= max_leg_length:
        max_leg_length = min_leg_length

    usemodes_modal = dash.no_update

    if any(trigger_id == f"{key}_use" for key in names_all_modes):
        if not any([walk_use, cycle_use, bus_use, drive_use]):
            walk_use = cycle_use = bus_use = drive_use = usemodes_modal = [True]

# These two could be done only when triggered but not costly:
    locomotion_vals = \
        {"walk":  {"speed": walk_speed, "cost": walk_cost, "exercise": walk_exercise,
            "use": walk_use},
        "cycle": {"speed": cycle_speed, "cost": cycle_cost, "exercise": cycle_exercise,
            "use": cycle_use},
        "bus": {"speed": bus_speed, "cost": bus_cost, "exercise": bus_exercise,
            "use": bus_use},
        "drive": {"speed": drive_speed, "cost": drive_cost, "exercise": drive_exercise,
            "use": drive_use}}

    weight_vals = \
        {"weight_cost":  {
            "weight": None if weight_cost_hardsoft == "hard" else weight_cost,
            "penalty": weight_cost_penalty},
         "weight_time": {
            "weight": None if weight_time_hardsoft == "hard" else weight_time,
            "penalty": weight_time_penalty},
         "weight_slope": {
            "weight": None if weight_slope_hardsoft == "hard" else weight_slope,
            "penalty": weight_slope_penalty}}

    return trigger_id, max_leg_length, min_leg_length, \
        walk_use, cycle_use, bus_use, drive_use, usemodes_modal, \
        formatting.state_to_json(locomotion_vals), formatting.state_to_json(weight_vals)

@app.callback(
    [Output(f"{graph.lower()}_graph", "figure") for graph in ["Space", "Time", "Feasibility"]],
    Input("solutions_print_code", "value"),
    Input("problem_print_code", "value"),
    [State("locomotion_state", "children")])
def display_graphics(solutions_print_code, problem_print_code, locomotion_state):
    """Generate graphics for legs and samples."""

    trigger = dash.callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    legs = formatting.tour_from_json(problem_print_code)

    if trigger_id == "solutions_print_code":
        try:
            sampleset = formatting.sampleset_from_json(solutions_print_code)
        except JSONDecodeError:
            sampleset = None    # For cancelled/failed jobs
    else:
        sampleset = None

    locomotion_vals = formatting.state_from_json(locomotion_state)

    fig_space = graphics.plot_space(legs, sampleset)
    fig_time = graphics.plot_time(legs, locomotion_vals, sampleset)
    fig_feasiblity = graphics.plot_feasiblity(legs, locomotion_vals, sampleset)

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
            status = jobs.cancel(client, job_id)
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

    if formatting.job_status_to_str(job_submit_state) == "SUBMITTED":
        return  dict(), True, True, True, True

    if formatting.job_status_to_str(job_submit_state) == "PENDING":
        return  dict(), False, True, True, True

    elif formatting.job_status_to_str(job_submit_state) == "IN_PROGRESS":
        return dict(display="none"), True, dash.no_update, dash.no_update, \
            dash.no_update

    elif any(formatting.job_status_to_str(job_submit_state) == status for status in jobs.TERMINATED):
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
        return jobs.job_bar["READY"][0], jobs.job_bar["READY"][1]
    else:
        state = formatting.job_status_to_str(job_submit_state)
        return jobs.job_bar[state][0], jobs.job_bar[state][1]

@app.callback(
    Output("job_id", "children"),
    [Input("job_submit_time", "children")],
    [State("problem_print_code", "value")],
    [State("max_leg_slope", "value")],
    [State(id, "value") for id in names_budget_inputs],
    [State("weights_state", "children")],
    [State("locomotion_state", "children")],
    [State("max_runtime", "value")],)
def submit_job(job_submit_time, problem_print_code, max_leg_slope,
    max_cost, max_time,  weights_state, locomotion_state, max_runtime):
    """Submit job and provide job ID."""

    trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger_id =="job_submit_time":

        solver = client.get_solver(supported_problem_types__issuperset={"cqm"})

        weight_vals = formatting.state_from_json(weights_state)
        locomotion_vals = formatting.state_from_json(locomotion_state)
        legs = formatting.tour_from_json(problem_print_code)

        cqm = build_cqm(legs, max_leg_slope, max_cost, max_time,
            weight_vals, locomotion_vals)

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

    if any(formatting.job_status_to_str(job_submit_state) == status for status in jobs.TERMINATED):
        if formatting.job_status_to_str(job_submit_state) == "COMPLETED":
            sampleset = client.retrieve_answer(job_id).sampleset
            return formatting.sampleset_to_json(sampleset), formatting.solutions_to_display(sampleset)
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
            formatting.job_status_to_display("SUBMITTED"), submit_time, f"Elapsed: 0 sec."

    if any(formatting.job_status_to_str(job_submit_state) == status for status in
        ["SUBMITTED", *jobs.RUNNING]):

        job_submit_state = jobs.get_status(client, job_id, job_submit_time)
        if not job_submit_state:
            job_submit_state = "SUBMITTED"
            wd_time = 0.2*1000
        else:
            wd_time = 1*1000

        elapsed_time = jobs.elapsed(job_submit_time)

        return True, False, wd_time, 0, \
            formatting.job_status_to_display(job_submit_state), dash.no_update, \
            f"Elapsed: {elapsed_time} sec."

    if any(formatting.job_status_to_str(job_submit_state) == status for status in jobs.TERMINATED):

        elapsed_time = jobs.elapsed(job_submit_time)
        disable_btn = False
        disable_watchdog = True

        return disable_btn, disable_watchdog, 0.1*1000, 0, \
            dash.no_update, dash.no_update, f"Elapsed: {elapsed_time} sec."

    else:   # Exception state: should only ever happen in testing
        return False, True, 0, 0, formatting.job_status_to_display("ERROR"), dash.no_update, \
            "Please restart"

if __name__ == "__main__":
    app.run_server(debug=True)
