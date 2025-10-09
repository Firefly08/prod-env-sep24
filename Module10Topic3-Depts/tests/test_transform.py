import pandas as pd
import pytest
from pipeline.transform import select_keep_cols, sanity_checks

def test_select_keep_cols_ok(good_df):
    keep = ["action_taken", "respondent_id"]
    trimmed = select_keep_cols(good_df, keep)
    assert list(trimmed.columns) == keep
    assert len(trimmed) == len(good_df)

def test_select_keep_cols():
    df = pd.DataFrame({'a':[1], 'b':[2]})
    with pytest.raises(ValueError) as e:
        select_keep_cols(df, ['a', 'c'])
    assert "Missing columns" in str(e.value)

def test_sanity_checks_pass(good_df):
    # all constraints satisfied
    sanity_checks(good_df)

def test_sanity_checks_fail_on_neg_income(bad_df_neg_income):
    with pytest.raises(ValueError) as e:
        sanity_checks(bad_df_neg_income)
    assert "applicant_income_000s" in str(e.value)

def test_sanity_checks_fail_on_nulls(good_df):
    bad = good_df.copy()
    bad.loc[0, "respondent_id"] = None
    with pytest.raises(ValueError, match=r"Some value[s]? in respondent_id are missing"):
        sanity_checks(bad)

def test_sanity_checks_fail_on_invalid_action(good_df):
    bad = good_df.copy()
    bad.loc[0, "action_taken"] = 99
    with pytest.raises(ValueError, match=r"Unexpected value[s]? in action_taken(?:.*1-8)?"):
        sanity_checks(bad)
