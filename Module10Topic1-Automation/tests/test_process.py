import pandas as pd


def test_pipeline(path:str):

    df = pd.DataFrame({
        "action_taken": [1, 2, 3],
        "state_abbr": ["CA", "NY", "TX"],
        "respondent_id": ["123", "456", "789"],
        "loan_amount_000s": [100, 200, 300],
        "applicant_income_000s": [50, 60, 70],
    })
    