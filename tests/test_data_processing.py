import pandas as pd
import pytest
from utils.data_processing import TransactionValidationError, validate_transactions

def good(): return pd.DataFrame({"ticker":["aapl","AAPL"],"date":["2024-01-01","2024-02-01"],"transaction_type":["Buy","Sell"],"quantity":[2,1],"price":[100,110]})
def test_valid_normalizes_and_orders(): assert list(validate_transactions(good()).ticker)==["AAPL","AAPL"]
def test_missing_column():
    with pytest.raises(TransactionValidationError): validate_transactions(good().drop(columns="price"))
@pytest.mark.parametrize("column,value",[("transaction_type","Hold"),("quantity",-1),("price",0),("date","nope")])
def test_bad_fields(column,value):
    f=good(); f.loc[0,column]=value
    with pytest.raises(TransactionValidationError): validate_transactions(f)
def test_oversell():
    f=good(); f.loc[1,"quantity"]=3
    with pytest.raises(TransactionValidationError,match="attempted to sell"): validate_transactions(f)
