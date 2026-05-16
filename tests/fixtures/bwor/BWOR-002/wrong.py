import gurobipy as gp
from gurobipy import GRB


_PRICE = {
    "feed_1": 0.2,
    "feed_2": 0.7,
    "feed_3": 0.4,
    "feed_4": 0.3,
    "feed_5": 0.8,
}


def build_model(data: dict) -> gp.Model:
    model = gp.Model("BWOR-002-wrong")
    feeds = data["feeds"]
    amount = model.addVars(feeds, lb=0.0, name="feed")

    for nutrient, requirement in data["requirements"].items():
        model.addConstr(
            gp.quicksum(data["nutrients"][nutrient][feed] * amount[feed] for feed in feeds) >= requirement,
            name=f"requirement_{nutrient}",
        )

    model.setObjective(gp.quicksum(_PRICE[feed] * amount[feed] for feed in feeds), GRB.MINIMIZE)
    return model
