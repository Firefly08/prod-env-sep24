# pipeline/validation.py
import pandas as pd

def _select_keep_cols(df: pd.DataFrame, keep_cols: list[str]) -> pd.DataFrame:
    """
    Select only the columns in keep_cols from the DataFrame.
    Raises ValueError if any required column is missing.
    """
    missing = [c for c in keep_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df[keep_cols]


def _sanity_checks(df: pd.DataFrame) -> None:
    """
    Run basic data validation checks on the filtered DataFrame.
    Raises ValueError if data quality issues are found.
    """
    # At least 90% of applicant_income_000s must be >= 0
    if (df["applicant_income_000s"] >= 0).mean() < 0.90:
        raise ValueError(
            "More than 10% of applicant_income_000s are missing or negative"
        )

    # No nulls in critical columns
    for col in ["action_taken", "respondent_id"]:
        if df[col].isna().sum() > 0:
            raise ValueError(f"Some values in {col} are missing")

    # action_taken must only contain values 1–8
    if not df["action_taken"].isin(range(1, 9)).all():
        raise ValueError("Unexpected value in action_taken")
