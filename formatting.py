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

from tour_planning import weight_ranges, budget_ranges

__all__ = ["job_status_to_str", "tour_from_json",
    "job_status_to_display",  "tour_to_display", "tour_to_json",
    "locomotion_to_display", "solutions_to_display",
    "sampleset_to_json", "sampleset_from_json", "cqm_to_display",
    "state_from_json", "state_to_json"]

def job_status_to_display(code):
    """Output status as 'Status: <status>'."""

    return f"Status: {code}"

def job_status_to_str(human_readable):
    """Strip status from 'Status: <status>'"""

    return human_readable.split()[1]

def tour_to_display(problem):
    """Output problem for humans."""

    df = pd.DataFrame(problem)
    return df.to_string()

def tour_to_json(problem):
    """Output problem for code."""

    return json.dumps(problem)

def tour_from_json(code):
    """Input problem from code."""

    return json.loads(code)

def locomotion_to_display(boundaries):
    """Output locomotion for humans."""

    first_lines = f"""Costs for this tour range from {boundaries['cost_min']} to {boundaries['cost_max']}.
Times for this tour range from {boundaries['time_min']} to {boundaries['time_max']}.

Average cost is {boundaries['cost_avg']}.
Average time is {boundaries['time_avg']}.
"""

    return first_lines

def solutions_to_display(sampleset):
    """Output solutions for humans."""

    s = ""
    sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
    if len(sampleset_feasible) == 0:
        return "No feasible solutions found."
    first = sorted({int(key.split('_')[1]): key.split('_')[0] for key,val in \
        sampleset_feasible.first.sample.items() if val==1.0}.items())
    ratio = round(len(sampleset_feasible)/len(sampleset), 3)
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

    return dimod.SampleSet.from_serializable(json.loads(saved_sampleset))

def cqm_to_display(cqm):
    """Output CQM for humans."""

    one_hots_str = ""
    for key, val in cqm.constraints.items():
        if "One-hot" in key:
            one_hots_str += "\n\t" + key + ": " + val.to_polystring()

    slope_str = ""
    for key, val in cqm.constraints.items():
        if "Too steep" in key:
            slope_str += "\n\t" + key + ": " + val.to_polystring()

    toll_str = ""
    for key, val in cqm.constraints.items():
        if "Toll to drive" in key:
            toll_str += "\n\t" + key + ": " + val.to_polystring()

    print_str = "Objective (Maximize Exercise):\n\n\t" + cqm.objective.to_polystring()
    print_str += "\n\nCost Constraint: \n\n\t" + cqm.constraints["Total cost"].to_polystring()
    print_str += "\n\nTime Constraint: \n\n\t" + cqm.constraints["Total time"].to_polystring()
    print_str += "\n\nSlope Constraints: \n" + slope_str
    print_str += "\n\nSingle-Locomotion-Mode-Per-Leg Constraints: \n" + one_hots_str
    print_str += "\n\nToll Booth Constraints: \n" + toll_str

    return print_str

def state_to_json(locomotion_vals):
    """Output locomotion state for code rereading."""

    return json.dumps(locomotion_vals)

def state_from_json(locomotion_json):
    """input locomotion state from saved."""

    return json.loads(locomotion_json)
