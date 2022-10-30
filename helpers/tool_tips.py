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

from tour_planning import (leg_ranges, budget_ranges, weight_ranges, locomotion_ranges,
    names_locomotion_inputs, MAX_SOLVER_RUNTIME)
from dash import html

tool_tips = {"num_legs":
f"""Number of legs for the tour. Displays in the bar graph below as the number
of its sections. [Range: {leg_ranges['num_legs']}]""",
    "max_leg_length":
f"""Maximum length for a single leg. Leg lengths are randomly set to be no greater
than this value. The bar graph below displays leg length as relative widths of
the sections. [Range: {leg_ranges['max_leg_length']}]""",
    "min_leg_length":
f"""Minimum length for a single leg. Leg lengths are randomly set to be no shorter
than this value. The bar graph below displays leg length as relative widths of
the sections. [Range: {leg_ranges['min_leg_length']}]""",
    "max_leg_slope":
"""Maximum slope you wish to climb on your own (walking or cycling). Leg slopes
are randomly set between zero and 10. This value's effect on the selection of
walking or cycling for steep legs depends also on your constraint setting for
slope.""",
    "max_cost":
f"""Maximum you wish to pay for the tour. Cost per leg depends on the selected
modes of locomotion; e.g., walking is cheaper than driving. Together with your
configuration of the cost constraint, discourages (soft constraint) or disallows
(hard constraint) a selection of locomotion modes such that the total cost of the
tour exceed this value. [Range: {budget_ranges['max_cost']}]""",
    "max_time":
f"""Maximum time you wish the entire tour to last. Time per leg depends on the
selected modes of locomotion; e.g., walking is slower than driving. Together with
your configuration of the time constraint, discourages (soft constraint) or disallows
(hard constraint) a selection of locomotion modes such that the total duration of
the tour exceed this value.[Range: {budget_ranges['max_time']}]""",
    "weight_cost":
f"""Weight you assign to the constraint on highest cost. When you set the cost
constraint as soft, a higher weight compared to other soft constraints (time and
slope) increases the relative importance of meeting the value set for the budgeted
cost. Ignored when you set the cost constraint as hard.
[Range: {weight_ranges['weight_cost']}]""",
    "weight_cost_penalty":
"""Linear or quadratic soft constraint on highest cost. Linear constraints add a
penalty that scales linearly to its violation while the penalty for quadratic
constraints scales by the square of its violation; for example, selecting the
binary variable representing (expensive) driving on a long leg can carry a penalty
either proportional to the length of the leg or to the square of that length.
Ignored when you set the cost constraint as hard.""",
    "weight_cost_hardsoft":
f"""Hard or soft constraint on highest cost. When hard, input value is ignored.
See the README file for information about hard and soft constraints.""",
    "weight_time":
f"""Weight you assign to the constraint on longest tour duration. When you set
the time constraint as soft, a higher weight compared to other soft constraints
(cost and slope) increases the relative importance of meeting the value set for
the budgeted time. Ignored when you set the time constraint as hard.
[Range: {weight_ranges['weight_time']}]""",
    "weight_time_penalty":
"""Linear or quadratic soft constraint on longest tour duration. Linear constraints
add a penalty that scales linearly to its violation while the penalty for quadratic
constraints scales by the square of its violation; for example, selecting the
binary variable representing (slow) walking on a long leg can carry a penalty
either proportional to the length of the leg or to the square of that length.
Ignored when you set the time constraint as hard.""",
    "weight_time_hardsoft":
"""Hard or soft constraint on longest tour duration. When hard, input value is
ignored. See the README file for information about hard and soft constraints.""",
    "weight_slope":
f"""Weight you assign to the constraint on steepest leg to climb on your own.
When you set the slope constraint as soft, a higher weight compared to other soft
constraints (cost and time) increases the relative importance of not walking or
cycling on legs steeper than the value you set for steepest leg. Ignored when you
set the slope constraint as hard. [Range: {weight_ranges['weight_slope']}]""",
    "weight_slope_penalty":
"""Linear or quadratic soft constraint on steepest leg to cycle. Linear constraints
add a penalty that scales linearly to its violation while the penalty for quadratic
constraints scales by the square of its violation; for example, selecting the
binary variable representing cycling on a steep leg can carry a penalty
either proportional to the length of the leg or to the square of that length.
Ignored when you set the slope constraint as hard.""",
    "weight_slope_hardsoft":
"""Hard or soft constraint on on steepest leg to cycle. When hard, input value is
ignored. See the README file for information about hard and soft constraints.""",
    "btn_solve_cqm": "Click to submit your problem to a Leap quantum-classical hybrid CQM solver.",
    "btn_cancel": "Click to try cancel your problem before problem begins processing.",
    "max_runtime": f"Maximum runtime for the solver to process the problem. The default is 5 seconds. The maximum {MAX_SOLVER_RUNTIME} secs.",
    "constraint_settings_row":
[html.Div(["""Configure the constraints that encourage (soft constraints) or ensure (hard
constraints) solutions meet your budgeted cost and time for the tour and discourage
or prevent cycling on steep legs.""", html.Br(),
"See the README file for information about hard and soft constraints."])],
    "tour_settings_row":
[html.Div(["""Configure the tour's legs and budgets. Changes to the legs are
immediately reflected in the bar graph below. How your values for the tour budget
(highest cost and longest time) and greatest leg slope affect the solution
depends also on your constraint settings.""", html.Br(),
"See the README file for more information."])],
    "tab_for_Graph":
"""Displays the configured tour, as a colored bar divided into segments representing
the legs, and any found solutions as icons above the colored bar or written onto
the bar.""",
    "tab_for_Problem":
"""Displays the legs of the tour (length, slope, and toll booths), formatted for
reading and for copying into your code.""",
    "tab_for_Solutions":
"""Displays the best solution found, formatted for reading and as
  a dimod sampleset for copying into your code.""",
    "tab_for_CQM":
"""Displays the constrained quadratic model generated for your configured
  tour and constraints.""",
    "tab_for_Locomotion":
"""Displays information about your configured tour, such as the minimum, maximum,
and average values of cost and time, and information about the available modes
of locomotion.""",
    "graph_space":
"""Displays your configured tour, with leg distance as relative length and
elevation as color. Any toll booths are represented by icons above the tour.
Displays best found modes of locomotion as icons below the tour.""",
    "graph_time":
"""Displays relative leg duration as the widths of the bar's colored segments and,
for the best found solution, the cost per leg as a color heatmap.""",
    "graph_feasibility":
"""Displays feasible and non-feasible solutions in a three-dimensional plot of
exercise, cost, and time. Non-feasible solutions violate one or more hard
constraints; feasible solutions may violate some soft constraints.""",
    "tollbooths_active":
"""When set to 'On', tollbooths are added randomly with likelihood 20% to legs.
The generated CQM has a hard constraint to not drive on legs with tollbooths.""",}

tips_cost = f"""Cost per length unit for a mode of locomotion. This value multiplied
by the length of the leg gives the cost of that leg for this mode of locomotion.
[Range: {locomotion_ranges['walk_cost']}]"""
tool_tips_cost = {name: tips_cost for name in names_locomotion_inputs if "cost"
    in name}
tool_tips.update(tool_tips_cost)

tips_speed = f"Speed for a mode of locomotion. [Range: {locomotion_ranges['walk_speed']}]"
tool_tips_speed = {name: tips_speed for name in names_locomotion_inputs if "speed"
    in name}
tool_tips.update(tool_tips_speed)

tips_exercise = f"""Exercise coefficient for a mode of locomotion. This value multiplied
by the length of the leg and by its slope gives the cost of that leg for this mode
of locomotion. [Range: {locomotion_ranges['walk_exercise']}]"""
tool_tips_exercise = {name: tips_exercise for name in names_locomotion_inputs if "exercise"
    in name}
tool_tips.update(tool_tips_exercise)
