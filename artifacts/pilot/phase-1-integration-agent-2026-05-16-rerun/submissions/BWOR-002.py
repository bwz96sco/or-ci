import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    feeds = list(data["feeds"])
    price = data["price"]
    nutrients = data["nutrients"]
    requirements = data["requirements"]

    model = gp.Model("feed_selection")
    feed_kg = model.addVars(feeds, lb=0.0, vtype=GRB.CONTINUOUS, name="feed_kg")

    model.setObjective(
        gp.quicksum(float(price[feed]) * feed_kg[feed] for feed in feeds),
        GRB.MINIMIZE,
    )

    for nutrient, minimum_required in requirements.items():
        nutrient_content = nutrients[nutrient]
        model.addConstr(
            gp.quicksum(float(nutrient_content[feed]) * feed_kg[feed] for feed in feeds)
            >= float(minimum_required),
            name=f"min_{nutrient}",
        )

    return model
