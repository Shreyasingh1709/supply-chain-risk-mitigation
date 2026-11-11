
def investigate_stockout_risk(product_data):
    """
    Investigates operational context behind an ML stockout prediction.
    Uses observed dataset features, not future information.
    """

    findings = []

    probability = float(product_data["stockout_probability"])

    # Previous observed day's stockout status
    if int(product_data["stockout_label"]) == 1:
        findings.append(
            "The product experienced a stockout on the previous observed day."
        )
    else:
        findings.append(
            "The product did not experience a stockout on the previous observed day."
        )

    # Sales information
    sales = float(product_data["sale_amount"])
    findings.append(
        f"Recorded sales amount for the observed day: {sales:.2f}."
    )

    # Discount information
    discount = float(product_data["discount"])
    if discount > 0:
        findings.append(
            f"A discount of {discount:.2f} was recorded."
        )
    else:
        findings.append("No discount was recorded.")

    # Holiday and activity indicators
    if int(product_data["holiday_flag"]) == 1:
        findings.append("The observed day was marked as a holiday.")

    if int(product_data["activity_flag"]) == 1:
        findings.append("A promotional or activity event was recorded.")

    # Weather context
    findings.append(
        f"Weather observations: rainfall={float(product_data['precpt']):.2f}, "
        f"temperature={float(product_data['avg_temperature']):.2f}, "
        f"humidity={float(product_data['avg_humidity']):.2f}, "
        f"wind={float(product_data['avg_wind_level']):.2f}."
    )

    return {
        "stockout_probability": probability,
        "investigation_findings": findings
    }
