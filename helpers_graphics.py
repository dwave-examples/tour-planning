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
import pandas as pd
import plotly.express as px

from formatting import *

__all__ = ["plot_space", "plot_time", "plot_diversity"]

def plot_space(legs, samples=None):
    """Plot legs versus distance and slope, optionally with solutions."""

    df_legs = pd.DataFrame({"Length": [l["length"] for l in legs],
                            "Slope": [s["uphill"] for s in legs]})
    df_legs["Tour"] = 0

    fig = px.bar(df_legs, x="Length", y="Tour", color="Slope", orientation="h",
                 color_continuous_scale=px.colors.diverging.Geyser)

    fig.add_layout_image(
            dict(source="assets/europe.png", xref="x", yref="y", x=0, y=0.5,
            sizex=df_legs["Length"].sum(), sizey=1, sizing="stretch",
            opacity=0.25, layer="below"))

    x_pos = 0
    for indx, leg in enumerate(legs):
        if leg["toll"]:
            fig.add_layout_image(dict(source=f"assets/toll.png", xref="x",
                yref="y", x=x_pos, y=0.2, sizex=2, sizey=2, opacity=1, layer="above"))
        x_pos += df_legs["Length"][indx]

    fig.update_xaxes(showticklabels=True, title="Distance")
    fig.update_yaxes(showticklabels=False, title=None, range=(-0.5, 0.5))
    fig.update_traces(width=.1)
    fig.update_layout(font_color="rgb(6, 236, 220)", margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)")

    if samples:

        fig.update_traces(texttemplate = [transport for leg,transport in samples["first"]],
            textposition = "inside")

        x_pos = 0
        for leg, icon in samples["first"]:
            fig.add_layout_image(dict(source=f"assets/{icon}.png", xref="x",
            yref="y", x=x_pos, y=-0.1, sizex=2, sizey=2, opacity=1, layer="above"))
            x_pos += df_legs["Length"][leg]

    return fig

def plot_time(legs, transport, samples):
    """Plot legs versus time and cost given solutions."""

    if not samples:
        return None

    df_legs = pd.DataFrame({"Time": [l["length"]/transport[f[1]]["Speed"] for
        l,f in zip(legs, samples["first"])],
        "Cost": [transport[f[1]]["Speed"] for f in samples["first"]]})
    df_legs["Tour"] = 0

    fig = px.bar(df_legs, x="Time", y="Tour", color="Cost", orientation="h",
        color_continuous_scale=px.colors.diverging.Geyser)

    fig.add_layout_image(
        dict(source="assets/clock.png", xref="x", yref="y", x=0, y=0.5,
        sizex=df_legs["Time"].sum(), sizey=1, sizing="stretch",
        opacity=0.25, layer="below"))

    fig.update_xaxes(showticklabels=True, title="Time")
    fig.update_yaxes(showticklabels=False, title=None, range=(-0.5, 0.5))
    fig.update_traces(width=.1)
    fig.update_layout(font_color="rgb(6, 236, 220)",
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)")

    fig.update_traces(texttemplate = [transport for leg,transport in samples["first"]],
        textposition = "inside")

    x_max = df_legs["Time"].max()
    x_pos = 0
    for leg, icon in samples["first"]:
        fig.add_layout_image(dict(source=f"assets/{icon}.png", xref="x",
            yref="y", x=x_pos, y=-0.1, sizex=x_max/10, sizey=x_max/10, opacity=1,
            layer="above"))
        x_pos += df_legs["Time"][leg]

    return fig

def plot_diversity(legs, transport, samples):
    """Plot solutions."""

    if not samples:
        return None

    #Done only once per job submission but can move to NumPy if slow
    data = {"Cost": [], "Time": [], "Energy": [], "Feasibility": []}
    for sample, energy, feasability in samples["sampleset"].data(fields=["sample", "energy", "is_feasible"]):
        locomotion_per_leg = sorted({int(key.split("_")[1]): key.split("_")[0] for
            key,val in sample.items() if val==1.0}.items())
        data["Cost"].append(sum(transport[f[1]]["Speed"] for f in locomotion_per_leg))
        data["Time"].append(sum(l["length"]/transport[f[1]]["Speed"] for l,f in zip(legs, locomotion_per_leg)))
        data["Energy"].append(energy)
        data["Feasibility"].append(feasability)

    df = pd.DataFrame(data)

    occurrences = df.groupby(df.columns.tolist(),as_index=False).size()
    color = ["blue" if f==True else "black" for f in occurrences["Feasibility"]]
    legend_names = {"blue":"Feasible", "black": "Infeasible"}

    fig = px.scatter_3d(occurrences, x="Time", y="Cost", z="Energy", color=color,
        size=occurrences["size"])

    fig.for_each_trace(lambda t: t.update(name = legend_names[t.name],
        legendgroup = legend_names[t.name]))
    fig.update_scenes(xaxis_title_text="Time",
                      yaxis_title_text="Cost",
                      zaxis_title_text="Exercise")
    fig.update_layout(font_color="rgb(6, 236, 220)",
        margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")

    return fig
