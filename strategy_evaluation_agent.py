
def evaluate_strategies(risk_level, investigation_findings):

    strategies = []

    # Strategy 1: Inventory inspection
    if any("stockout" in finding.lower()
           and "experienced a stockout" in finding.lower()
           for finding in investigation_findings):

        strategies.append({
            "strategy": "Immediate inventory inspection",
            "priority_score": 95,
            "reason": "A stockout was observed on the previous day."
        })

    else:
        strategies.append({
            "strategy": "Routine inventory inspection",
            "priority_score": 85,
            "reason": "No previous-day stockout was observed."
        })

    # Strategy 2: Supplier coordination
    if risk_level == "High Risk":
        supplier_score = 95
    elif risk_level == "Medium Risk":
        supplier_score = 80
    else:
        supplier_score = 60

    strategies.append({
        "strategy": "Supplier coordination",
        "priority_score": supplier_score,
        "reason": "Priority is based on the predicted stockout risk."
    })

    # Strategy 3: Replenishment planning
    if risk_level == "High Risk":
        replenishment_score = 100
    elif risk_level == "Medium Risk":
        replenishment_score = 85
    else:
        replenishment_score = 55

    strategies.append({
        "strategy": "Replenishment planning",
        "priority_score": replenishment_score,
        "reason": "Priority is based on the predicted stockout risk."
    })

    # Rank strategies
    ranked_strategies = sorted(
        strategies,
        key=lambda x: x["priority_score"],
        reverse=True
    )

    return ranked_strategies
