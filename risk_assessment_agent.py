def assess_stockout_risk(probability):

    if probability >= 0.70:
        risk_level = "High Risk"
        recommendation = "Immediate inventory replenishment required."

    elif probability >= 0.45:
        risk_level = "Medium Risk"
        recommendation = "Monitor inventory and prepare replenishment."

    else:
        risk_level = "Low Risk"
        recommendation = "Continue normal inventory monitoring."

    return {
        "probability": probability,
        "risk_level": risk_level,
        "recommendation": recommendation
    }