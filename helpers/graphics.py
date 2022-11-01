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

import dimod

from tour_planning import _calculate_total

__all__ = ["plot_space", "plot_time", "plot_feasiblity"]


def _plot_background(fig, legs, df, x_axis, image):
    """Plot the background and tollboths. For Time, requires feasible sample."""

    fig.add_layout_image(
            dict(source=image, xref="x", yref="y", x=0, y=0.5,
            sizex=df[x_axis].sum(), sizey=1, sizing="stretch",
            opacity=0.5, layer="below"))

    x_pos = 0
    x_width = df[x_axis].sum()
    for indx, leg in enumerate(legs):
        if leg["toll"]:
            fig.add_layout_image(dict(source=f"assets/toll.png", xref="x",
                yref="y", x=x_pos, y=0.2, sizex=0.025*x_width, sizey=0.025*x_width,
                    opacity=1, layer="above"))
        x_pos += df[x_axis][indx]

    title = "Distance" if x_axis == "Length" else "Time"

    fig.update_xaxes(showticklabels=True, title=title)
    fig.update_yaxes(showticklabels=False, title=None, range=(-0.5, 0.5))
    fig.update_traces(width=.1)
    fig.update_layout(font_color="rgb(3, 184, 255)", margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)")

    return x_width

def get_first_feasible_sorted(sampleset):
    """Get first samples, preferably feasible."""

    sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
    if len(sampleset_feasible) > 0:
        first = sorted({int(key.split("_")[1]): key.split("_")[0] for key,val in \
            sampleset_feasible.first.sample.items() if val==1.0}.items())
    else:
        first = None

    return first

def _plot_results(fig, first, df, x_axis, x_width):
    """Add the best found, feasible solution to the graphics."""

    fig.update_traces(texttemplate = [locomotion for leg, locomotion in first],
        textposition = "inside")

    x_pos = 0
    for leg, icon in first:
        fig.add_layout_image(dict(source=f"assets/{icon}.png", xref="x",
        yref="y", x=x_pos, y=-0.1, sizex=0.025*x_width, sizey=0.025*x_width,
            opacity=1, layer="above"))
        x_pos += df[x_axis][leg]

def plot_space(legs, sampleset=None):
    """Plot legs versus distance and slope, optionally with solutions."""

    df_legs = pd.DataFrame({"Length": [l["length"] for l in legs],
                            "Slope": [s["uphill"] for s in legs]})
    df_legs["Tour"] = 0

    fig = px.bar(df_legs, x="Length", y="Tour", color="Slope", orientation="h",
                 color_continuous_scale=["#074C91", "#2A7DE1", "#17BEBB", "#FFA143", "#F37820"],
                 hover_data=["Length", "Slope"])    # looks like plotly bug (hover_data)

    x_width = _plot_background(fig, legs, df_legs, "Length", "assets/background_space.jpg")

    if sampleset:

        first = get_first_feasible_sorted(sampleset)

        if first:
            _plot_results(fig, first, df_legs, "Length", x_width)
        else:
             fig.add_annotation(x=0.1, y=0.85,  text="No feasible solutions found.",
                xref="paper", yref="paper", font=dict(size=18, color="red"),
                showarrow=False)

    return fig

def plot_time(legs, locomotion_vals, sampleset):
    """Plot legs versus time and cost given solutions."""

    if not sampleset:
        return px.bar()

    first = get_first_feasible_sorted(sampleset)

    if not first:
        return px.bar()

    df_legs = pd.DataFrame({"Time": [l["length"]/locomotion_vals[f[1]]["speed"] for
        l,f in zip(legs, first)],
        "Cost": [locomotion_vals[f[1]]["cost"] for f in first]})
    df_legs["Tour"] = 0

    fig = px.bar(df_legs, x="Time", y="Tour", color="Cost", orientation="h",
        color_continuous_scale=["#074C91", "#2A7DE1", "#17BEBB", "#FFA143", "#F37820"])

    x_width = _plot_background(fig, legs, df_legs, "Time", "assets/background_time.png")

    _plot_results(fig, first, df_legs, "Time", x_width)

    return fig

def plot_feasiblity(legs, locomotion_vals, sampleset):
    """Plot solutions."""

    if not sampleset:
        return px.bar()

    #Done only once per job submission but can move to NumPy if slow
    modes = [key for key in locomotion_vals.keys() if locomotion_vals[key]["use"]]
    t= [dimod.Binary(f"{mode}_{i}") for i in range(len(legs)) for mode in modes]

    data = {"Cost": [], "Time": [], "Exercise": [], "Energy": [], "Feasibility": []}
    for sample, energy, feasibility in sampleset.data(
        fields=["sample", "energy", "is_feasible"]):
        for measure in ["Cost", "Time", "Exercise"]:
            data[measure].append(_calculate_total(t, measure, legs, locomotion_vals).energy(sample))
        data["Energy"].append(energy)  # we're maximizing so switch symbol
        data["Feasibility"].append(feasibility)
    df = pd.DataFrame(data)

    occurrences = df.groupby(df.columns.tolist(),as_index=False).size()
    occurrences = occurrences.rename({"size": "Occurrences"}, axis=1)

    colors = ['blue', 'red']
    symbols = ['circle', 'x']
    if not occurrences.iloc[0]["Feasibility"]:
        colors = ['red', 'blue']
        symbols = ['x', 'circle']

    # Bugfix: plotly scatter_3d seems to get stuck on small numerical precission
    # so an energy of -23.600000000000072 is below rounded to say 3
    fig = px.scatter_3d(occurrences.round(3), x="Time", y="Cost", z="Exercise",
        color="Feasibility", size="Occurrences", size_max=50, symbol="Feasibility",
        color_discrete_sequence = colors, symbol_sequence= symbols,
        hover_data=["Cost", "Time", "Exercise", "Energy", "Occurrences"])

    fig.update_scenes(xaxis_title_text="Time",
                      yaxis_title_text="Cost",
                      zaxis_title_text="Exercise")
    fig.update_layout(font_color="rgb(3, 184, 255)",
        margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")

    return fig
