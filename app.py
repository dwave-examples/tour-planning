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
