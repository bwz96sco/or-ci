{
  "id": "BWOR-010",
  "problem_type": "LP",
  "instance": {
    "mills": ["I", "II", "III"],
    "factories": ["Factory 1", "Factory 2", "Factory 3"],
    "supply": {
      "I": 20,
      "II": 30,
      "III": 20
    },
    "processing_capacity": {
      "Factory 1": 15,
      "Factory 2": 25,
      "Factory 3": 20
    },
    "unit_transport_cost": {
      "I": {
        "Factory 1": 3,
        "Factory 2": 10,
        "Factory 3": 2
      },
      "II": {
        "Factory 1": 4,
        "Factory 2": 11,
        "Factory 3": 8
      },
      "III": {
        "Factory 1": 8,
        "Factory 2": 11,
        "Factory 3": 4
      }
    },
    "unit_processing_profit": {
      "Factory 1": 12,
      "Factory 2": 16,
      "Factory 3": 11
    },
    "unit_net_benefit": {
      "I": {
        "Factory 1": 9,
        "Factory 2": 6,
        "Factory 3": 9
      },
      "II": {
        "Factory 1": 8,
        "Factory 2": 5,
        "Factory 3": 3
      },
      "III": {
        "Factory 1": 4,
        "Factory 2": 5,
        "Factory 3": 7
      }
    },
    "objective": "maximize_total_net_benefit"
  },
  "metamorphic": {
    "cost_scaling": {
      "coefficient_paths": ["instance.unit_net_benefit"],
      "factors": [2.0],
      "tolerance_abs": 1e-6,
      "tolerance_rel": 1e-6
    },
    "constraint_relaxation": {
      "relaxations": [
        {
          "name": "processing_capacity_increase",
          "paths": ["instance.processing_capacity"],
          "factor": 1.2,
          "objective_relation": "non_decrease"
        },
        {
          "name": "mill_supply_increase",
          "paths": ["instance.supply"],
          "factor": 1.2,
          "objective_relation": "non_decrease"
        }
      ],
      "tolerance_abs": 1e-6,
      "tolerance_rel": 1e-6
    }
  }
}