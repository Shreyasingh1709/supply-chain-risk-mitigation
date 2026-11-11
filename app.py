import streamlit as st
import pandas as pd

from agent_orchestrator import run_agent_workflow

st.set_page_config(
    page_title="Supply Chain Risk Management",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Supply Chain Disruption Prediction")
st.subheader("Agentic AI-Based Risk Mitigation System")

st.divider()

# Load actual Databricks predictions
@st.cache_data
def load_predictions():
    return pd.read_csv("stockout_predictions.csv")

try:
    df = load_predictions()
except FileNotFoundError:
    st.error("Prediction CSV not found. Please download it first.")
    st.stop()

# Overall Risk Summary

st.header("Overall Stockout Risk Summary")

def classify_risk(probability):
    if probability >= 0.70:
        return "High Risk"
    elif probability >= 0.45:
        return "Medium Risk"
    else:
        return "Low Risk"

df["risk_level"] = df["stockout_probability"].apply(classify_risk)

risk_counts = df["risk_level"].value_counts()
risk_counts = risk_counts.reindex(
    ["High Risk", "Medium Risk", "Low Risk"],
    fill_value=0
)

st.subheader("Risk Distribution")
st.bar_chart(risk_counts)

col1, col2, col3 = st.columns(3)

col1.metric("High Risk", int(risk_counts.get("High Risk", 0)))
col2.metric("Medium Risk", int(risk_counts.get("Medium Risk", 0)))
col3.metric("Low Risk", int(risk_counts.get("Low Risk", 0)))

st.divider()

st.header("Select Product Prediction")

selected_index = st.selectbox(
    "Choose a prediction",
    options=df.index,
    format_func=lambda i: (
        f"Date: {df.loc[i, 'dt']} | "
        f"Store: {df.loc[i, 'store_id']} | "
        f"Product: {df.loc[i, 'product_id']}"
    )
)

selected_row = df.loc[selected_index]

st.write("### Selected Product Details")

col1, col2, col3 = st.columns(3)

col1.metric("City ID", int(selected_row["city_id"]))
col2.metric("Store ID", int(selected_row["store_id"]))
col3.metric("Product ID", int(selected_row["product_id"]))

probability = float(selected_row["stockout_probability"])

st.metric(
    "ML Model Stockout Probability",
    f"{probability * 100:.2f}%"
)

st.write(
    "ML Model Prediction:",
    "Stockout" if int(selected_row["predicted_stockout"]) == 1
    else "No Stockout"
)

st.divider()

if st.button("Assess Risk"):

    result = run_agent_workflow(selected_row.to_dict())

    st.session_state["result"] = result
    st.session_state["assessed_index"] = selected_index
    st.session_state["approval"] = "Pending"

if (
    "result" in st.session_state
    and st.session_state.get("assessed_index") == selected_index
):

    result = st.session_state["result"]

    st.subheader("Risk Assessment")

    risk = result["risk_assessment"]

    st.write("Risk Level:", risk["risk_level"])
    st.info(risk["recommendation"])

    st.subheader("Risk Investigation Findings")
    investigation = result["risk_investigation"]
    for finding in investigation["investigation_findings"]:
        st.write("🔎", finding)

    st.subheader("Mitigation Recommendations")

    for action in result["mitigation_actions"]:
        st.write("•", action)
    
    st.subheader("Strategy Evaluation and Ranking")

    for strategy in result["ranked_strategies"]:
        st.write(
            f"**{strategy['strategy']}**"
        )

        st.progress(
            strategy["priority_score"] / 100
        )
        
        st.write(
            f"Priority Score: {strategy['priority_score']}/100"
        )
        
        st.caption(strategy["reason"])
  

    st.divider()

    st.subheader("Human Approval")

    st.write(
        "Review the recommendations before approving them."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Approve Recommendations"):
            st.session_state["approval"] = "Approved"

    with col2:
        if st.button("Reject Recommendations"):
            st.session_state["approval"] = "Rejected"

    if st.session_state["approval"] == "Approved":
        st.success("Recommendations Approved!")

    elif st.session_state["approval"] == "Rejected":
        st.error("Recommendations Rejected!")

    else:
        st.warning("Awaiting Human Approval")