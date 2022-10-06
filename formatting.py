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
import json

import dimod

__all__ = ["job_status_to_str", "tour_from_json",
    "job_status_to_display",  "tour_to_display", "tour_to_json",
    "tour_params_to_df", "out_transport_human", "solutions_to_display",
    "sampleset_to_json", "sampleset_from_json"]

def job_status_to_str(human_readable):
    """Strip status from 'Status: <status>'"""

    return human_readable.split()[1]

def tour_from_json(code):
    """Input problem from code."""

    return json.loads(code)

def job_status_to_display(code):
    """Output status as 'Status: <status>'."""

    return f"Status: {code}"

def tour_to_display(problem):
    """Output problem for humans."""

    df = pd.DataFrame(problem)
    return df.to_string()

def tour_to_json(problem):
    """Output problem for code."""

    return json.dumps(problem)

def tour_params_to_df(params, last_changed):
    """Output the input ranges."""

    df = pd.DataFrame(params)
    df.fillna("HARD",inplace=True)
    last_change_row = df.shape[1]*[""]
    if last_changed:
        last_change_row[df.columns.get_loc(last_changed)] = "<<---"
    df.loc[len(df)] = last_change_row
    df_t = df.T
    df_t.columns = ["Min.", "Max.", "Current Value", "Last Updated Input"]

    header = f"""Configurable inputs have these supported ranges and current values:
"""
    return header + df_t.to_string()

out_transport_human = tour_to_display

def solutions_to_display(sampleset):
    """Output solutions for humans."""

    s = ""
    sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
    if len(sampleset_feasible) == 0:
        return "No feasible solutions found."
    first = sorted({int(key.split('_')[1]): key.split('_')[0] for key,val in \
        sampleset_feasible.first.sample.items() if val==1.0}.items())
    ratio = round(len(sampleset_feasible)/len(sampleset), 1)
    s += "Feasible solutions: {:.1%} of {} samples.\n".format((ratio), len(sampleset))
    s += f"Best solution with energy {round(sampleset_feasible.first.energy)} is:\n"
    for leg in first:
        s += f"{leg}\n"
    return s

def sampleset_to_json(sampleset):
    """Output solutions for code."""

    return json.dumps(sampleset.to_serializable())

def sampleset_from_json(saved_sampleset):
    """Retrieve saved sampleset."""

    sampleset = dimod.SampleSet.from_serializable(json.loads(saved_sampleset))
    sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
    if len(sampleset_feasible) == 0:
        return "No feasible solutions found."
    first = sorted({int(key.split("_")[1]): key.split("_")[0] for key,val in \
        sampleset_feasible.first.sample.items() if val==1.0}.items())

    return {"sampleset": sampleset, "feasible": sampleset_feasible, "first": first}
