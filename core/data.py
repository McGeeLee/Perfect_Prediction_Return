import tushare as ts
import yfinance as yf
import pandas as pd


def detect_asset(symbol):
    symbol = symbol.upper()

    # ===== Crypto =====
    if "-USD" in symbol:
        return "crypto", "Yahoo"

    # ===== A股 =====
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        code = symbol.split(".")[0]

        # ETF（51开头）
        if code.startswith("51"):
            return "etf", "Tushare"

        # 股票
        elif code.startswith(("6", "0", "3")):
            return "stock", "Tushare"

    # ===== 默认（美股等）=====
    return "other", "Yahoo"


def format_date_for_yahoo(date_str):
    # 把 20250101 → 2025-01-01
    if "-" not in date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str


def get_data(symbol, start, end, token=None):

    asset_type, source = detect_asset(symbol)
    print(f"识别: {asset_type} | 数据源: {source}")

    # =========================
    # Tushare
    # =========================
    if source == "Tushare":

        ts.set_token(token)
        pro = ts.pro_api()

        try:
            if asset_type == "stock":
                df = pro.daily(
                    ts_code=symbol,
                    start_date=start,
                    end_date=end
                )

            elif asset_type == "etf":
                df = pro.fund_daily(
                    ts_code=symbol,
                    start_date=start,
                    end_date=end
                )

            else:
                return pd.DataFrame()

        except Exception as e:
            print("Tushare报错:", e)
            return pd.DataFrame()

        if df is None or df.empty:
            print("Tushare返回空")
            return pd.DataFrame()

        df = df.sort_values("trade_date")
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        df.rename(columns={
            'open': 'Open',
            'close': 'Close'
        }, inplace=True)

        return df[['trade_date', 'Open', 'Close']]

    # =========================
    # Yahoo
    # =========================
    else:

        start = format_date_for_yahoo(start)
        end = format_date_for_yahoo(end)

        try:
            df = yf.download(
                symbol,
                start=start,
                end=end,
                interval="1d",
                progress=False
            )
        except Exception as e:
            print("Yahoo报错:", e)
            return pd.DataFrame()

        if df is None or df.empty:
            print("Yahoo返回空")
            return pd.DataFrame()

        # 👉 reset index
        df = df.reset_index()

        # 👉 关键1：处理 MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        print("列名:", df.columns.tolist())

        # 👉 关键2：列名兜底处理
        if "Date" in df.columns:
            df.rename(columns={"Date": "trade_date"}, inplace=True)

        # 有些情况是小写
        if "date" in df.columns:
            df.rename(columns={"date": "trade_date"}, inplace=True)

        # 👉 关键3：确保 Open/Close 存在
        if "Open" not in df.columns or "Close" not in df.columns:
            print("列缺失:", df.columns)
            return pd.DataFrame()

        return df[['trade_date', 'Open', 'Close']]
    