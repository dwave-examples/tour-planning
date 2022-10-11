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

from tour_planning import leg_ranges, budget_ranges, weight_ranges, MAX_SOLVER_RUNTIME

tool_tips = {"num_legs": f"Number of legs for the tour. [Range: {leg_ranges['num_legs']}]",
    "max_leg_length": f"Maximum length for a single leg.  [Range: {leg_ranges['max_leg_length']}]",
    "min_leg_length": f"Minimum length for a single leg.   [Range: {leg_ranges['min_leg_length']}]",
    "max_leg_slope": "Maximum elevation for a single leg.",
    "max_cost": f"Maximum you wish to pay for the tour. [Range: {budget_ranges['max_cost']}]",
    "max_time": f"Maximum time you wish the entire tour to last.  [Range: {budget_ranges['max_time']}]",
    "weight_cost": f"Weight you assign to the constraint on highest cost.  [Range: {weight_ranges['weight_cost']}]",
    "weight_cost_penalty": f"Linear or quadratic soft constraint on highest cost.",
    "weight_cost_hardsoft": f"Hard or soft constraint on highest cost. When hard, input value is ignored.",
    "weight_time": f"Weight you assign to the constraint on longest tour duration.  [Range: {weight_ranges['weight_time']}]",
    "weight_time_penalty": "Linear or quadratic soft constraint on longest tour duration.",
    "weight_time_hardsoft": "Hard or soft constraint on longest tour duration. When hard, input value is ignored",
    "weight_slope": f"Weight you assign to the constraint on steepest leg to cycle.  [Range: {weight_ranges['weight_slope']}]",
    "weight_slope_penalty": "Linear or quadratic soft constraint on steepest leg to cycle.",
    "weight_slope_hardsoft": "Hard or soft constraint on on steepest leg to cycle. When hard, input value is ignored",
    "btn_solve_cqm": "Click to submit your problem to a Leap quantum-classical hybrid CQM solver.",
    "btn_cancel": "Click to try cancel your problem before problem begins processing.",
    "max_runtime": f"Maximum runtime for the solver to process the problem. The default is 5 seconds. The maximum {MAX_SOLVER_RUNTIME} secs.",
}
