
from risk_assessment_agent import assess_stockout_risk
from risk_investigation_agent import investigate_stockout_risk
from mitigation_agent import recommend_mitigation
from strategy_evaluation_agent import evaluate_strategies


def run_agent_workflow(product_data):

    # Agent 1: Risk Assessment
    probability = float(product_data["stockout_probability"])
    risk_result = assess_stockout_risk(probability)

    # Agent 2: Risk Investigation
    investigation_result = investigate_stockout_risk(product_data)

    # Agent 3: Mitigation Planning
    recommendations = recommend_mitigation(
        risk_result["risk_level"]
    )

    # Agent 4: Strategy Evaluation
    ranked_strategies = evaluate_strategies(
        risk_result["risk_level"],
        investigation_result["investigation_findings"]
    )

    result = {
        "risk_assessment": risk_result,
        "risk_investigation": investigation_result,
        "mitigation_actions": recommendations,
        "ranked_strategies": ranked_strategies,
        "approval_status": "Pending Human Approval"
    }

    return result
