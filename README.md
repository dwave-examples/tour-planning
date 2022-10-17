# Tour Planning

A demonstration of using hard and soft constraints on the Leap&trade;
quantum-classical hybrid constrained quadratic (CQM) solver.

This example solves a problem of selecting, for a tour divided into several legs
of varying lengths and steepness, a combination of locomotion modes (walking,
cycling, bussing, and driving) such that one can gain the greatest benefit of
outdoor exercise while not exceeding one's budget of transportation costs and time.  

![Example Solution](assets/example_space_graph.png)

## Hard and Soft Constraints

Constraints for optimization problems are often categorized as either “hard” or
“soft”.

Any hard constraint  must be satisfied for a solution of the problem to qualify
as feasible. Soft constraints may be violated to achieve an overall good solution.

By setting appropriate weights to soft constraints in comparison to the objective
and to other soft constraints, you can express the relative importance of such
constraints.

This example enables you to set hard or soft constraints on the tour's cost, its
duration, and the steepest leg one can cycle. The CQM has hard constraints that
ensure a single mode of locomotion is selected for each leg and prevent driving
on legs with toll booths.  

## Installation

This example can be run in the Leap IDE by accessing the following URL:

    https://ide.dwavesys.io/#https://github.com/dwave-examples/tour-planning


Alternatively, install requirements locally. Ideally, in a virtual environment.

    pip install -r requirements.txt

## Usage

To run the demo:

```bash
python app.py
```

Access the user interface with your browser at http://127.0.0.1:8050/.

The demo program opens an interface where you can configure tour
problems, submit these problems to a CQM solver, and examine the results.

Hover over an input field to see a description of the input and its range of
supported values.

### Configuring the Tour

The upper-left section of the user interface lets you configure the tour: how
many legs it should comprise, lengths of these legs, and maximum elevation gain.
Additionally, you can configure your budgets of cost (modes of locomotion
vary in price) and time (walking is slower than driving) for the entire tour.

The lengths of each leg are set to a uniform random value between your selected
minimum and maximum lengths. Steepness is set uniformly at random between zero
and the maximum you set.

A leg's steepness affects cycling: a constraint is set to discourage (soft) or
disallow (hard) cycling on legs that exceed half the maximum slope you set.

When you update a tour's legs, toll booths are placed at random on some of the
legs. These affect driving in a private car (as opposed to taking a bus):
the generated CQM sets a hard constraint to not drive on legs with toll booths.

### Configuring the Constraints

The upper-middle section of the user interface lets you configure the constraints
on cost, time, and steepness.

You can select whether to use hard or soft constraints. For soft constraints,
you can set a weight and a type of penalty: linear or quadratic.

### Submitting the Problem for Solution

The upper-right section of the user interface lets you submit your problem
to a Leap hybrid CQM solver. The default solver runtime of 5 seconds is used
unless you choose to increase it.

### Viewing Solutions and Problem Information

The lower section presents information about the problem and any found solutions.
These are presented in the following tabs:

* **Graph:** displays the configured problem and any found solutions in three ways:

    - **Space:** displays leg lengths as relative lengths of the tour, slope as a
      color heatmap, and toll booths as icons above the tour. Modes of locomotion
      for found solutions are written onto the tour and displayed as icons below
      it.
    - **Time:** displays leg duration as relative lengths of the tour and leg pricing
      as a color heatmap.   
    - **Feasibility:** displays feasible and non-feasible solutions in a
      three-dimensional plot for exercise, cost, and time.
* **Problem:** displays the legs of the tour (length, slope, and toll booths), formatted
    for reading and for copying into your code.
* **Solutions:** displays the best solution found formatted for reading and the
    [dimod sampleset](
https://docs.ocean.dwavesys.com/en/stable/docs_dimod/reference/sampleset.html)
    for copying into your code.
* **CQM:** displays the constrained quadratic model generated for your configured
    tour and CQM settings.
* **Transport:** displays tour information for your configuration, such as the
    minimum, maximum, and average values of cost and time, and information about
    the available modes of locomotion.

## Model Overview

The problem of selecting a mode of locomotion for every leg of the tour to achieve
some objective (maximize exercise) given a number of constraints (e.g., do not
overpay) can be modeled as an optimization problem with decisions that could
either be true (or yes) or false (no): for any leg, should one drive? Should one
walk?

This model uses four binary variables for each leg of the tour, each one representing
whether one particular mode of locomotion is used or not. For example, leg
number 5 might have the following binary variables and values in one solution:

| Binary Variable        | Represents    | Value in a Particular Solution |
|------------------------|---------------|--------------------------------|
| ``walk_5``             | Walk leg 5    | False                          |
| ``cycle_5``            | Cycle leg 5   | True                           |
| ``bus_5``              | Bus leg 5     | False                          |
| ``drive_5``            | Drive leg 5   | False                          |

In the above case, the mode of locomotion selected for leg 5 is to cycle.

The CQM is built as follows with a single objective and several constraints:

* **Objective: Maximize Exercise**

    To maximize exercise on the tour, the CQM sets an objective to
    maximize the total values of exercise of all the tour legs. It does this in
    a summation over the following multiplicands for each leg:

    * length
    * slope
    * exercise value of each mode of locomotion
    * binary variable representing each mode of locomotion

    Because a single mode of locomotion is selected for each leg (as explained
    below), all the products but one are zeroed by the binary variables of that
    leg. For example, in leg 5 above, the length set for leg 5 is multiplied by
    its slope and the exercise value of cycling because only the binary variable
    for cycling is not zero.
* **Constraint 1: Single Mode of Locomotion Per Leg**

    To ensure a single mode of locomotion is selected for each
    leg, the sum of the binary variables representing each leg must equal one
    (a ["one-hot" constraint](https://docs.dwavesys.com/docs/latest/handbook_reformulating.html)). This is a hard constraint.
* **Constraint 2: Cost**

    To discourage or prevent the tour's cost from exceeding
    your configured value, the CQM sets a constraint that the total cost over
    all legs is less or equal to the desired cost. It does this in a summation
    over leg length multiplied by the cost value of each mode of locomotion and
    by the binary variable representing each mode of locomotion. Again, for each
    leg the only non-zero product is for the cost of the selected locomotion and
    the leg length. This can be a hard or soft constraint.
* **Constraint 3: Time**

    To discourage or prevent the tour's duration from exceeding your configured
    value, the CQM sets a constraint similar to that on cost but with the leg
    length divided by the value of speed for each mode of locomotion. This can be
    a hard or soft constraint.

* **Constraint 4: Toll Booths**

    To prevent the selection of driving on legs with toll booths, the CQM sets a
    constraint that the binary variable representing driving be zero for any leg
    with a toll booth. This is a hard constraint.

* **Constraint 4: Steep Legs**

    To discourage or prevent the selection of cycling on legs where the slope
    is steeper than half your configured maximum, the CQM sets a constraint that
    the binary variable representing cycling be zero for any such legs.
    This can be a hard or soft constraint.

## Code Overview

Most the code related to configuring the CQM is in the
[tour_planning.py](tour_planning.py) file. The remaining files mostly support
the user interface.

TODO: add math formulas for the model and names of the functions that implement
them.

---
**Note:** Standard practice for submitting problems to Leap solvers is to use
a [dwave-system](https://docs.ocean.dwavesys.com/en/stable/docs_system/sdk_index.html)
sampler; for example, you typically use
[LeapHybridCQMSampler](https://docs.ocean.dwavesys.com/en/stable/docs_system/reference/samplers.html)
for CQM problems. The code in this example uses the
[dwave-cloud-client](https://docs.ocean.dwavesys.com/en/stable/docs_cloud/sdk_index.html),
which enables finer control over communications with the Solver API (SAPI).

If you are learning to submit problems to Leap solvers, use a ``dwave-system``
solver, with its higher level of abstraction and thus greater simplicity,
as demonstrated in most the code examples of the
[example collection](https://github.com/dwave-examples) and in the
[Ocean documentation](https://docs.ocean.dwavesys.com/en/stable/index.html).


---

## License

Released under the Apache License 2.0. See [LICENSE](LICENSE) file.
