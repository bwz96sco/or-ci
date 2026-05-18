import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    flour_mills = data["flour_mills"]
    factories = data["factories"]
    flour_mill_output = data["flour_mill_output"]
    factory_capacity = data["factory_capacity"]
    unit_transportation_cost = data["unit_transportation_cost"]
    unit_processing_profit = data["unit_processing_profit"]

    model = gp.Model("BWOR-010")

    allocation = model.addVars(
        flour_mills,
        factories,
        lb=0.0,
        vtype=GRB.CONTINUOUS,
        name="allocation",
    )

    for mill_idx, mill in enumerate(flour_mills):
        model.addConstr(
            gp.quicksum(allocation[mill, factory] for factory in factories)
            <= float(flour_mill_output[mill]),
            name=f"mill_output_{mill_idx}",
        )

    for factory_idx, factory in enumerate(factories):
        model.addConstr(
            gp.quicksum(allocation[mill, factory] for mill in flour_mills)
            <= float(factory_capacity[factory]),
            name=f"factory_capacity_{factory_idx}",
        )

    total_benefit = gp.quicksum(
        (
            float(unit_processing_profit[factory])
            - float(unit_transportation_cost[mill][factory])
        )
        * allocation[mill, factory]
        for mill in flour_mills
        for factory in factories
    )

    sense = str(data.get("objective_sense", "maximize")).lower()
    model.setObjective(total_benefit, GRB.MAXIMIZE if sense == "maximize" else GRB.MINIMIZE)

    return model
