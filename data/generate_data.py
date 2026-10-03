"""Generate a synthetic telecom customer dataset with realistic churn drivers.

The data is synthetic (no real customers) but follows patterns commonly seen
in telecom churn studies: short tenure, month-to-month contracts, high monthly
charges, fiber internet without tech support and electronic-check payments all
raise churn risk.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_CUSTOMERS = 7000


def generate(n: int = N_CUSTOMERS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    contract = rng.choice(["Month-to-month", "One year", "Two year"], n, p=[0.55, 0.21, 0.24])
    max_tenure = np.select(
        [contract == "Month-to-month", contract == "One year"], [36, 60], default=72
    )
    tenure = np.clip((rng.beta(1.2, 2.0, n) * max_tenure).round().astype(int) + 1, 1, 72)

    internet = rng.choice(["DSL", "Fiber optic", "No"], n, p=[0.34, 0.44, 0.22])
    has_internet = internet != "No"

    def addon(p):
        return np.where(has_internet, np.where(rng.random(n) < p, "Yes", "No"), "No internet service")

    online_security = addon(0.35)
    tech_support = addon(0.35)
    streaming_tv = addon(0.45)

    payment = rng.choice(
        ["Electronic check", "Mailed check", "Bank transfer", "Credit card"],
        n,
        p=[0.34, 0.23, 0.22, 0.21],
    )
    senior = (rng.random(n) < 0.16).astype(int)
    partner = np.where(rng.random(n) < 0.48, "Yes", "No")
    paperless = np.where(rng.random(n) < 0.59, "Yes", "No")

    base = np.select([internet == "Fiber optic", internet == "DSL"], [70.0, 45.0], default=20.0)
    monthly = (
        base
        + (online_security == "Yes") * 6
        + (tech_support == "Yes") * 6
        + (streaming_tv == "Yes") * 10
        + rng.normal(0, 4, n)
    ).round(2)
    total = (monthly * tenure * rng.uniform(0.95, 1.05, n)).round(2)

    logit = (
        -1.6
        + 1.3 * (contract == "Month-to-month")
        - 1.2 * (contract == "Two year")
        - 0.045 * tenure
        + 0.9 * (internet == "Fiber optic")
        - 0.6 * (tech_support == "Yes")
        - 0.5 * (online_security == "Yes")
        + 0.7 * (payment == "Electronic check")
        + 0.4 * senior
        - 0.3 * (partner == "Yes")
        + 0.3 * (paperless == "Yes")
        + 0.012 * (monthly - 60)
    )
    churn = np.where(rng.random(n) < 1 / (1 + np.exp(-logit)), "Yes", "No")

    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{i:05d}" for i in range(1, n + 1)],
            "senior_citizen": senior,
            "partner": partner,
            "tenure_months": tenure,
            "contract": contract,
            "internet_service": internet,
            "online_security": online_security,
            "tech_support": tech_support,
            "streaming_tv": streaming_tv,
            "paperless_billing": paperless,
            "payment_method": payment,
            "monthly_charges": monthly,
            "total_charges": total,
            "churn": churn,
        }
    )


if __name__ == "__main__":
    out = Path(__file__).parent / "telco_churn.csv"
    df = generate()
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows to {out} | churn rate: {(df.churn == 'Yes').mean():.1%}")
