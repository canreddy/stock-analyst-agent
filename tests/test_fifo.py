import pandas as pd
from utils.portfolio_math import fifo_match
def tx(rows): return pd.DataFrame(rows,columns=["ticker","date","transaction_type","quantity","price"]).assign(date=lambda x:pd.to_datetime(x.date))
def test_required_fifo_case():
    h,s=fifo_match(tx([("AAPL","2024-01-01","Buy",10,100),("AAPL","2024-01-02","Buy",10,120),("AAPL","2024-01-03","Sell",15,150)])); assert h.iloc[0].quantity==5 and h.iloc[0].cost_basis==600 and s.iloc[0].realized_pl==650
def test_liquidation_and_repurchase():
    h,s=fifo_match(tx([("A","2024-01-01","Buy",2,10),("A","2024-01-02","Sell",2,15),("A","2024-01-03","Buy",3,20)])); assert h.iloc[0].cost_basis==60 and s.iloc[0].realized_pl==10
def test_interleaved_tickers_and_multiple_sales():
    h,s=fifo_match(tx([("A","2024-01-01","Buy",5,10),("B","2024-01-02","Buy",3,20),("A","2024-01-03","Sell",2,12),("A","2024-01-04","Sell",1,13)])); assert set(h.ticker)=={"A","B"} and s.realized_pl.sum()==7
