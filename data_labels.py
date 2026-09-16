import pandas as pd
from scipy.stats import spearmanr

def add_forward_returns(df: pd.DataFrame, horizons:list[float]) -> pd.DataFrame:
    df = df.sort_values('time').reset_index(drop=True)

    for h in horizons:
        future_df = df[['time', 'mid_price']].copy()
        future_df = future_df.rename(columns={'mid_price': 'mid_price_future'})
        future_df['time'] = future_df['time'] - h

        merged = pd.merge_asof(
            df.sort_values('time'),
            future_df.sort_values('time'),
            on='time',
            direction='forward'
        )

        df[f'fwd_returns_{h}s'] = merged['mid_price_future'] - merged['mid_price']

        pass
    return df  
