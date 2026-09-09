'''
obi.py

Order Book Imbalance (OBI) Calculation.

Range: -1 (all sell pressure) to +1 (all buy pressure), 0 = balanced
Computed at different depths: how many price levels on each side to sum volume over before computing.
'''


import pandas as pd
import numpy as np

def compute_obi(df: pd.DataFrame, depth: int) -> pd.Series:
    '''
    compute obi at a given depth for every row in df.

    parameters
    ----------
    df: DataFrame from lobster_loader.load_lobster_day(), must contain 
    columns ask_size_1, depth and bid_size_1

    depth: how many book levels to sum volume over (1, 5 or 10)

    Returns
    -------
    Series of OBI values, same index as df. NaN where volume sums to 0(both sides empty), works as a gard
    '''
    ask_cols = [f"ask_size_{i}" for i in range(1, depth+1)]
    bid_cols = [f"bid_size_{i}" for i in range(1, depth+1)]

    missing = [c for c in ask_cols + bid_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing columns for depth={depth}: {missing}"
        )

    bid_vol = df[bid_cols].sum(axis=1)
    ask_vol = df[ask_cols].sum(axis=1)

    denom = bid_vol + ask_vol
    obi = (bid_vol - ask_vol)/denom
    obi = obi.where(denom != 0, np.nan)
    return obi 

def add_obi_columns(df: pd.DataFrame, depths: list[int] = [1, 5, 10]) -> pd.DataFrame:
    df = df.copy()
    for d in depths:
        df[f"obi_depth{d}"] = compute_obi(df, depth=d)
    return df 

if __name__ == "__main__":
    from lobster_loader import load_lobster_day, add_mid_price

    msg_path =  "data/AAPL_2012-06-21_34200000_57600000_message_10.csv"
    book_path = "data/AAPL_2012-06-21_34200000_57600000_orderbook_10.csv"

    df = load_lobster_day(msg_path, book_path, n_levels=10)
    df = add_mid_price(df)
    df = add_obi_columns(df, depths=[1, 5, 10])

    print(df[["time", "mid_price", "obi_depth5", "obi_depth10"]].head(10))
    print("\nOBI summary stats:")
    print(df[["obi_depth1", "obi_depth5", "obi_depth10"]].describe())
