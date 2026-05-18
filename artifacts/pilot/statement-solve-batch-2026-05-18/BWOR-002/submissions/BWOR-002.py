import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    feeds = data["feeds"]
    prices = data["price_dollars_per_kg"]
    protein = data["protein_g_per_kg"]
    minerals = data["minerals_g_per_kg"]
    vitamins = data["vitamins_mg_per_kg"]
    requirements = data["minimum_requirements"]

    model = gp.Model("BWOR_002_feed_selection")
    model.Params.OutputFlag = 0

    feed_kg = model.addVars(feeds, lb=0.0, vtype=GRB.CONTINUOUS, name="feed_kg")

    model.addConstr(
        gp.quicksum(protein[f] * feed_kg[f] for f in feeds)
        >= requirements["protein_g"],
        name="minimum_protein",
    )
    model.addConstr(
        gp.quicksum(minerals[f] * feed_kg[f] for f in feeds)
        >= requirements["minerals_g"],
        name="minimum_minerals",
    )
    model.addConstr(
        gp.quicksum(vitamins[f] * feed_kg[f] for f in feeds)
        >= requirements["vitamins_mg"],
        name="minimum_vitamins",
    )

    model.setObjective(
        gp.quicksum(prices[f] * feed_kg[f] for f in feeds),
        GRB.MINIMIZE,
    )

    return model
