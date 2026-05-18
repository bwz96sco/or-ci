import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    brands = data["brands"]
    raw_materials = data["raw_materials"]
    selling_price = data["selling_price"]
    processing_cost = data["processing_cost"]
    raw_material_cost = data["raw_material_cost"]
    monthly_usage_limit = data["monthly_usage_limit"]
    minimum_content_fraction = data.get("minimum_content_fraction", {})
    maximum_content_fraction = data.get("maximum_content_fraction", {})

    model = gp.Model("BWOR_001_candy_blending")

    production = model.addVars(brands, lb=0.0, name="production")
    material_used = model.addVars(raw_materials, brands, lb=0.0, name="material_used")

    for brand in brands:
        model.addConstr(
            production[brand] == gp.quicksum(material_used[material, brand] for material in raw_materials),
            name=f"blend_balance_{brand}",
        )

    for material in raw_materials:
        model.addConstr(
            gp.quicksum(material_used[material, brand] for brand in brands)
            <= monthly_usage_limit[material],
            name=f"monthly_limit_{material}",
        )

    for material, brand_limits in minimum_content_fraction.items():
        for brand, fraction in brand_limits.items():
            model.addConstr(
                material_used[material, brand] >= fraction * production[brand],
                name=f"min_content_{material}_{brand}",
            )

    for material, brand_limits in maximum_content_fraction.items():
        for brand, fraction in brand_limits.items():
            model.addConstr(
                material_used[material, brand] <= fraction * production[brand],
                name=f"max_content_{material}_{brand}",
            )

    revenue = gp.quicksum(selling_price[brand] * production[brand] for brand in brands)
    processing = gp.quicksum(processing_cost[brand] * production[brand] for brand in brands)
    material_cost = gp.quicksum(
        raw_material_cost[material] * material_used[material, brand]
        for material in raw_materials
        for brand in brands
    )

    model.setObjective(revenue - processing - material_cost, GRB.MAXIMIZE)
    return model
