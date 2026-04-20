import numpy as np

def run_strategy(df, fee, freq):

    df = df.copy()

    if freq == "Year":
        df['Group'] = df['trade_date'].dt.year
    elif freq == "Month":
        df['Group'] = df['trade_date'].dt.to_period('M')
    elif freq == "Day":
        df['Group'] = df['trade_date'].dt.date
    else:
        raise ValueError("Invalid freq")

    grouped = df.groupby('Group').agg({
        'Open': 'first',
        'Close': 'last'
    }).dropna()

    grouped['bh_return'] = grouped['Close'] / grouped['Open']

    grouped['abs_return'] = abs((grouped['Close'] - grouped['Open']) / grouped['Open'])

    grouped['net_return'] = grouped['abs_return'] - 2 * fee

    grouped['trade'] = grouped['net_return'] > 0

    grouped['strategy_return'] = np.where(
        grouped['trade'],
        1 + grouped['net_return'],
        1
    )

    grouped['bh_cum'] = grouped['bh_return'].cumprod()
    grouped['strategy_cum'] = grouped['strategy_return'].cumprod()

    return grouped.reset_index()
