def recommend_mitigation(risk_level):

    if risk_level == "High Risk":
        actions = [
            "Prioritize immediate stock replenishment.",
            "Contact the supplier to arrange urgent delivery.",
            "Check alternative suppliers if stock is unavailable.",
            "Notify the inventory manager."
        ]

    elif risk_level == "Medium Risk":
        actions = [
            "Monitor current inventory levels.",
            "Contact the supplier to confirm delivery schedules.",
            "Prepare a replenishment order.",
            "Review upcoming product demand."
        ]

    else:
        actions = [
            "Continue regular inventory monitoring.",
            "Maintain normal replenishment schedules.",
            "Review daily stock levels."
        ]

    return actions