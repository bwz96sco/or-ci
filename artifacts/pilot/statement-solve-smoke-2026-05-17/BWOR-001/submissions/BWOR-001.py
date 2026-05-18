import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    brands = data["brands"]
    materials = data["materials"]
    selling_price = data["selling_price"]
    processing_cost = data["processing_cost"]
    raw_cost = data["raw_cost"]
    raw_limit = data["raw_limit"]
    minimum_fraction = data.get("minimum_fraction", {})
    maximum_fraction = data.get("maximum_fraction", {})

    model = gp.Model("BWOR-001")

    use = model.addVars(materials, brands, lb=0.0, name="use")
    production = model.addVars(brands, lb=0.0, name="production")

    for brand in brands:
        model.addConstr(
            production[brand] == gp.quicksum(use[material, brand] for material in materials),
            name=f"production_balance_{brand}",
        )

    for material in materials:
        model.addConstr(
            gp.quicksum(use[material, brand] for brand in brands) <= raw_limit[material],
            name=f"raw_limit_{material}",
        )

    for brand in brands:
        for material, fraction in minimum_fraction.get(brand, {}).items():
            model.addConstr(
                use[material, brand] >= fraction * production[brand],
                name=f"min_fraction_{material}_{brand}",
            )
        for material, fraction in maximum_fraction.get(brand, {}).items():
            model.addConstr(
                use[material, brand] <= fraction * production[brand],
                name=f"max_fraction_{material}_{brand}",
            )

    revenue = gp.quicksum(selling_price[brand] * production[brand] for brand in brands)
    brand_processing_cost = gp.quicksum(
        processing_cost[brand] * production[brand] for brand in brands
    )
    material_cost = gp.quicksum(
        raw_cost[material] * use[material, brand]
        for material in materials
        for brand in brands
    )

    model.setObjective(revenue - brand_processing_cost - material_cost, GRB.MAXIMIZE)
    return model
