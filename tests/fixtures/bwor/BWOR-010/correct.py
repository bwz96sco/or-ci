import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    model = gp.Model("BWOR-010-correct")
    mills = data["mills"]
    factories = data["factories"]
    shipped = model.addVars(mills, factories, lb=0.0, name="ship")

    for mill in mills:
        model.addConstr(
            gp.quicksum(shipped[mill, factory] for factory in factories) <= data["supply"][mill],
            name=f"supply_{mill}",
        )

    for factory in factories:
        model.addConstr(
            gp.quicksum(shipped[mill, factory] for mill in mills) <= data["capacity"][factory],
            name=f"capacity_{factory}",
        )

    model.setObjective(
        gp.quicksum(
            (data["profit"][factory] - data["transport_cost"][mill][factory]) * shipped[mill, factory]
            for mill in mills
            for factory in factories
        ),
        GRB.MAXIMIZE,
    )
    return model
