import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    model = gp.Model("BWOR-001-correct")
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
        data["selling_price"][brand] * gp.quicksum(quantity[material, brand] for material in materials)
        for brand in brands
    )
    processing = gp.quicksum(
        data["processing_cost"][brand] * gp.quicksum(quantity[material, brand] for material in materials)
        for brand in brands
    )
    raw_cost = gp.quicksum(
        data["raw_cost"][material] * quantity[material, brand] for material in materials for brand in brands
    )
    model.setObjective(revenue - processing - raw_cost, GRB.MAXIMIZE)
    return model
