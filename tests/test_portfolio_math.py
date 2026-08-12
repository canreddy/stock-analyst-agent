import numpy as np
import pandas as pd
from utils.portfolio_math import calculate_xirr, concentration_metrics, fifo_match, performance_summary
def transactions(): return pd.DataFrame({"ticker":["A","A","A"],"date":pd.to_datetime(["2024-01-01","2024-02-01","2024-03-01"]),"transaction_type":["Buy","Buy","Sell"],"quantity":[10,10,15],"price":[100,120,150]})
def table(): return pd.DataFrame({"ticker":["A","B"],"market_value":[750,250],"unrealized_pl":[150,-50],"portfolio_weight":[.75,.25]})
def test_summary_and_concentration():
    _,sales=fifo_match(transactions()); result=performance_summary(transactions(),sales,table()); c=concentration_metrics(table())
    assert result["total_investment"]==2200 and result["total_sell_proceeds"]==2250 and result["realized_pl"]==650 and result["total_economic_pl"]==1050
    assert c["largest_holding_pct"]==.75 and c["top_3_holding_pct"]==1 and c["hhi"]==.625
def test_xirr_valid_and_invalid():
    assert np.isfinite(calculate_xirr(pd.DataFrame({"ticker":["A"],"date":pd.to_datetime(["2024-01-01"]),"transaction_type":["Buy"],"quantity":[1],"price":[100]}),110,pd.Timestamp("2025-01-01")))
    assert np.isnan(calculate_xirr(pd.DataFrame({"ticker":["A"],"date":pd.to_datetime(["2024-01-01"]),"transaction_type":["Buy"],"quantity":[1],"price":[100]}),0,pd.Timestamp("2025-01-01")))
