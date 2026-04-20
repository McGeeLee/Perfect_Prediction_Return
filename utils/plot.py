import matplotlib.pyplot as plt

def plot_equity(df):

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(df['bh_cum'].values, label="Buy & Hold")
    ax.plot(df['strategy_cum'].values, label="Strategy")

    ax.set_title("Strategy vs Buy & Hold")
    ax.set_xlabel("Time")
    ax.set_ylabel("Growth")
    ax.legend()
    ax.grid()

    return fig