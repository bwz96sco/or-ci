import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    feeds = list(data["feeds"])
    price = data["price"]
    nutrients = data["nutrients"]
    requirements = data["requirements"]

    model = gp.Model("BWOR_002_feed_selection")

    feed_amount = model.addVars(
        feeds,
        lb=0.0,
        vtype=GRB.CONTINUOUS,
        name="feed_kg",
    )

    model.setObjective(
        gp.quicksum(price[feed] * feed_amount[feed] for feed in feeds),
        GRB.MINIMIZE,
    )

    for nutrient, requirement in requirements.items():
        model.addConstr(
            gp.quicksum(nutrients[nutrient][feed] * feed_amount[feed] for feed in feeds)
            >= requirement,
            name=f"min_{nutrient}",
        )

    return model
