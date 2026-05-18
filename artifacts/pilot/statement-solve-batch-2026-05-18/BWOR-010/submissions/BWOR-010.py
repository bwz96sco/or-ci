import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    mills = list(data["mills"])
    factories = list(data["factories"])
    mill_output = data["mill_output"]
    factory_capacity = data["factory_capacity"]
    unit_profit = data["unit_profit"]
    transport_cost = data["transport_cost"]

    model = gp.Model("BWOR-010")

    shipment = model.addVars(mills, factories, lb=0.0, name="shipment")

    for mill in mills:
        model.addConstr(
            gp.quicksum(shipment[mill, factory] for factory in factories)
            <= mill_output[mill],
            name=f"mill_output_{mill}",
        )

    for factory in factories:
        model.addConstr(
            gp.quicksum(shipment[mill, factory] for mill in mills)
            <= factory_capacity[factory],
            name=f"factory_capacity_{factory}",
        )

    net_benefit = gp.quicksum(
        (unit_profit[factory] - transport_cost[mill][factory])
        * shipment[mill, factory]
        for mill in mills
        for factory in factories
    )
    model.setObjective(net_benefit, GRB.MAXIMIZE)

    return model
