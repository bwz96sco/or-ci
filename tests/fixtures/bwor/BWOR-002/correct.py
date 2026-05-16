import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    model = gp.Model("BWOR-002-correct")
    feeds = data["feeds"]
    amount = model.addVars(feeds, lb=0.0, name="feed")

    for nutrient, requirement in data["requirements"].items():
        model.addConstr(
            gp.quicksum(data["nutrients"][nutrient][feed] * amount[feed] for feed in feeds) >= requirement,
            name=f"requirement_{nutrient}",
        )

    model.setObjective(gp.quicksum(data["price"][feed] * amount[feed] for feed in feeds), GRB.MINIMIZE)
    return model
