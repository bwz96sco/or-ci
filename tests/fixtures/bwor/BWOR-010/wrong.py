import gurobipy as gp
from gurobipy import GRB


_PROFIT = {
    "factory_1": 12,
    "factory_2": 16,
    "factory_3": 11,
}
_TRANSPORT_COST = {
    "mill_1": {"factory_1": 3, "factory_2": 10, "factory_3": 2},
    "mill_2": {"factory_1": 4, "factory_2": 11, "factory_3": 8},
    "mill_3": {"factory_1": 8, "factory_2": 11, "factory_3": 4},
}


def build_model(data: dict) -> gp.Model:
    model = gp.Model("BWOR-010-wrong")
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
            (_PROFIT[factory] - _TRANSPORT_COST[mill][factory]) * shipped[mill, factory]
            for mill in mills
            for factory in factories
        ),
        GRB.MAXIMIZE,
    )
    return model
