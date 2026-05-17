import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    mills = data["mills"]
    factories = data["factories"]
    supply = data["supply"]
    capacity = data["capacity"]
    transport_cost = data["transport_cost"]
    profit = data["profit"]

    model = gp.Model("BWOR_010_flour_allocation")
    model.Params.OutputFlag = 0

    shipped = model.addVars(
        mills,
        factories,
        lb=0.0,
        vtype=GRB.CONTINUOUS,
        name="ship",
    )

    for mill in mills:
        model.addConstr(
            gp.quicksum(shipped[mill, factory] for factory in factories)
            <= supply[mill],
            name=f"supply_{mill}",
        )

    for factory in factories:
        model.addConstr(
            gp.quicksum(shipped[mill, factory] for mill in mills)
            <= capacity[factory],
            name=f"capacity_{factory}",
        )

    model.setObjective(
        gp.quicksum(
            (profit[factory] - transport_cost[mill][factory]) * shipped[mill, factory]
            for mill in mills
            for factory in factories
        ),
        GRB.MAXIMIZE,
    )

    return model
