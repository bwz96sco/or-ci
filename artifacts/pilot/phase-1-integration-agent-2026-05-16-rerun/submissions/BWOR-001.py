import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    model = gp.Model("BWOR_001")

    brands = list(data["brands"])
    materials = list(data["materials"])

    production = model.addVars(brands, lb=0.0, name="production")
    use = model.addVars(materials, brands, lb=0.0, name="use")

    for brand in brands:
        model.addConstr(
            production[brand] == gp.quicksum(use[material, brand] for material in materials),
            name=f"production_balance[{brand}]",
        )

    for material in materials:
        model.addConstr(
            gp.quicksum(use[material, brand] for brand in brands)
            <= data["raw_limit"][material],
            name=f"raw_limit[{material}]",
        )

    for brand, requirements in data.get("minimum_fraction", {}).items():
        for material, fraction in requirements.items():
            model.addConstr(
                use[material, brand] >= fraction * production[brand],
                name=f"min_fraction[{brand},{material}]",
            )

    for brand, requirements in data.get("maximum_fraction", {}).items():
        for material, fraction in requirements.items():
            model.addConstr(
                use[material, brand] <= fraction * production[brand],
                name=f"max_fraction[{brand},{material}]",
            )

    revenue = gp.quicksum(
        data["selling_price"][brand] * production[brand] for brand in brands
    )
    processing = gp.quicksum(
        data["processing_cost"][brand] * production[brand] for brand in brands
    )
    raw_material = gp.quicksum(
        data["raw_cost"][material] * use[material, brand]
        for material in materials
        for brand in brands
    )

    model.setObjective(revenue - processing - raw_material, GRB.MAXIMIZE)
    return model
