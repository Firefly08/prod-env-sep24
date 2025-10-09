import pandas as pd
import pytest
from pipeline.transform import select_keep_cols, sanity_checks

def test_select_keep_cols_ok():
    df = pd.DataFrame({"a":[1], "b":[2]})
    out = select_keep_cols(df.rename(columns={"a":"action_taken","b":"respondent_id"}),
                           ["action_taken", "respondent_id"])
    assert list(out.columns) == ["action_taken", "respondent_id"]

def test_sanity_checks_negative_income():
    df = pd.DataFrame({
        "action_taken":[1,1,1],
        "respondent_id":["x","y","z"],
        "applicant_income_000s":[-1,-2,-3],
    })
    with pytest.raises(ValueError):
        sanity_checks(df)