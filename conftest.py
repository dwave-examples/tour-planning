# Used instead of setting Python path for pytest file discovery
import pytest

import dimod

@pytest.fixture
def locomotion_data_default():

    return {
    "walk": {"speed": 1, "cost": 0, "exercise": 1, "use": True},
    "cycle": {"speed": 3, "cost": 2, "exercise": 2, "use": True},
     "bus": {"speed": 4, "cost": 3, "exercise": 0, "use": True},
     "drive": {"speed": 7, "cost": 5, "exercise": 0, "use": True}}

@pytest.fixture
def tour_data_default_2_legs():

    return  [{"length": 5.3, "uphill": 7.0, "toll": False},
             {"length": 5.6, "uphill": 2.9, "toll": False}]

@pytest.fixture
def tour_data_simple():

    return  [{"length": 1, "uphill": 1.0, "toll": False}]

@pytest.fixture
def samplesets_feasible_infeasible():

    sampleset = dimod.SampleSet.from_samples([
        {"bus_0": 0, "drive_0": 1, "cycle_0": 0, "walk_0": 0,
         "bus_1": 0, "drive_1": 0, "cycle_1": 0, "walk_1": 1},
        {"bus_0": 0, "drive_0": 0, "cycle_0": 0, "walk_0": 1,
         "bus_1": 1, "drive_1": 0, "cycle_1": 0, "walk_1": 0}], "BINARY", [0, 0])
    sampleset = dimod.append_data_vectors(sampleset, is_satisfied=[[True], [True]])
    sampleset_feasible = dimod.append_data_vectors(sampleset, is_feasible=[True, True])
    sampleset_infeasible = dimod.append_data_vectors(sampleset, is_feasible=[False, False])

    return {"feasible": sampleset_feasible, "infeasible": sampleset_infeasible}

@pytest.fixture
def weight_data_default():

    return {
    "weight_cost":  {"weight": None, "penalty": "linear"},
    "weight_time": {"weight": 44, "penalty": "linear"},
    "weight_slope": {"weight": 55, "penalty": "quadratic"}}
