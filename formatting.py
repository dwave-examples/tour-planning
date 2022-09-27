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

__all__ = ["out_job_submit_state", "in_job_submit_state", "out_problem_human",
    "out_problem_code", "in_problem_code", "out_input_human", "out_transport_human",
    "out_solutions_human",]

def out_job_submit_state(code):
    """Output status as 'Status: <status>'."""
    return f"Status: {code}"

def in_job_submit_state(human_readable):
    """Strip status from 'Status: <status>'"""
    return human_readable.split()[1]

def out_problem_human(problem):
    """Output problem for humans."""
    df = pd.DataFrame(problem)
    return df.to_string()

out_transport_human = out_problem_human

def out_problem_code(problem):
    """Output problem for code."""
    return json.dumps(problem)

def in_problem_code(code):
    """Input problem from code."""
    return json.loads(code)

def out_input_human(params):
    """Output input ranges for humans."""
    df = pd.DataFrame(params)
    df_t = df.T
    df_t.columns = ["Min.", "Max.", "Current Value"]
    return df_t.to_string()

def out_solutions_human(sampleset):
    """Output solutions for humans."""
    s = ""
    sampleset_feasible = sampleset.filter(lambda row: row.is_feasible)
    first = sorted({int(key.split('_')[1]): key.split('_')[0] for key,val in \
        sampleset_feasible.first.sample.items() if val==1.0}.items())
    ratio = round(len(sampleset_feasible)/len(sampleset), 1)
    s += "Feasible solutions: {:.1%} of {} samples.\n".format((ratio), len(sampleset))
    s += f"Best solution with energy {round(sampleset_feasible.first.energy)} is:\n"
    for leg in first:
        s += f"{leg}\n"
    return s
