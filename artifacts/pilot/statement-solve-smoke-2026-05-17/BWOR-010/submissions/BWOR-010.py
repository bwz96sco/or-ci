import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    mills = data["mills"]
    factories = data["factories"]
    supply = data["supply"]
    processing_capacity = data["processing_capacity"]
    unit_net_benefit = data["unit_net_benefit"]

    model = gp.Model("BWOR-010")

    shipment = model.addVars(mills, factories, lb=0.0, name="shipment")

    for mill in mills:
        model.addConstr(
            gp.quicksum(shipment[mill, factory] for factory in factories)
            <= supply[mill],
            name=f"supply_{mill}",
        )

    for factory in factories:
        safe_factory_name = factory.replace(" ", "_")
        model.addConstr(
            gp.quicksum(shipment[mill, factory] for mill in mills)
            <= processing_capacity[factory],
            name=f"processing_capacity_{safe_factory_name}",
        )

    model.setObjective(
        gp.quicksum(
            unit_net_benefit[mill][factory] * shipment[mill, factory]
            for mill in mills
            for factory in factories
        ),
        GRB.MAXIMIZE,
    )

    return model
