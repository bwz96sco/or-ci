import gurobipy as gp
from gurobipy import GRB


_SELLING_PRICE = {"x": 3.4, "y": 2.85, "z": 2.25}
_PROCESSING_COST = {"x": 0.5, "y": 0.4, "z": 0.3}
_RAW_COST = {"a": 2.0, "b": 1.5, "c": 1.0}


def build_model(data: dict) -> gp.Model:
    model = gp.Model("BWOR-001-wrong")
    materials = data["materials"]
    brands = data["brands"]
    quantity = model.addVars(materials, brands, lb=0.0, name="q")

    for material in materials:
        model.addConstr(
            gp.quicksum(quantity[material, brand] for brand in brands) <= data["raw_limit"][material],
            name=f"raw_limit_{material}",
        )

    for brand in brands:
        product = gp.quicksum(quantity[material, brand] for material in materials)
        for material, fraction in data["minimum_fraction"][brand].items():
            model.addConstr(quantity[material, brand] >= fraction * product, name=f"min_{material}_{brand}")
        for material, fraction in data["maximum_fraction"][brand].items():
            model.addConstr(quantity[material, brand] <= fraction * product, name=f"max_{material}_{brand}")

    revenue = gp.quicksum(
        _SELLING_PRICE[brand] * gp.quicksum(quantity[material, brand] for material in materials) for brand in brands
    )
    processing = gp.quicksum(
        _PROCESSING_COST[brand] * gp.quicksum(quantity[material, brand] for material in materials)
        for brand in brands
    )
    raw_cost = gp.quicksum(_RAW_COST[material] * quantity[material, brand] for material in materials for brand in brands)
    model.setObjective(revenue - processing - raw_cost, GRB.MAXIMIZE)
    return model
