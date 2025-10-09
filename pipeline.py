import pandas as pd

KEEP_COLS = [
    "action_taken",
    "state_abbr",
    "respondent_id",
    "loan_amount_000s",
    "applicant_income_000s"
]

def _sanity_checks(df: pd.DataFrame) -> None:
    if  (df["applicant_income_000s"] >= 0).mean() < 0.90:
        assert  False, "More than 10% of applicant_income_000s is negative"
    for col in ["action_taken", "respondent_id"]:
        if df[col].isna().sum() > 0:
            assert False, f"Some value in {col} are missing"
    if not df["action_taken"].isin(list(range(1, 9))).all():
        assert False, "action_taken has unexpected values"  
        
df_sample = pd.read_csv(
    'Download-Sample/2010HMDA_1.csv.gz', compression='gzip', nrows=10_000, low_memory=False
)

def _select_keep_cols(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in KEEP_COLS if c not in df.columns]
    if cols:
        raise ValueError(f"Missing columns: {cols}")
    return df[KEEP_COLS] 

def main():
    df_sample = pd.read_csv(
        'sample_2010HMDA.csv.gz', compression='gzip', nrows=10_000, low_memory=False
    )
    df_samp_filt = _select_keep_cols(df_sample)
    df_samp_filt.to_csv('filt_2010HMDA.csv.gz', compression='gzip', index=False)
    
if __name__ == "__main__":
    main()