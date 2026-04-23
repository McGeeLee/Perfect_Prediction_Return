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
        if code.startswith("51"):
            return "etf", "Tushare"
        elif code.startswith(("6", "0", "3")):
            return "stock", "Tushare"
    # ===== 默认（美股等）=====
    return "other", "Yahoo"

def format_date_for_yahoo(date_str):
    if "-" not in date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

def get_data(symbol, start, end, token=None):
    asset_type, source = detect_asset(symbol)
    print(f"识别: {asset_type} | 数据源: {source}")

    if source == "Tushare":
        ts.set_token(token)
        pro = ts.pro_api()
        try:
            if asset_type == "stock":
                df = pro.daily(ts_code=symbol, start_date=start, end_date=end)
            elif asset_type == "etf":
                df = pro.fund_daily(ts_code=symbol, start_date=start, end_date=end)
            else:
                return pd.DataFrame()
        except Exception as e:
            print("Tushare报错:", e)
            return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.sort_values("trade_date")
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.rename(columns={'open': 'Open', 'close': 'Close'}, inplace=True)
        return df[['trade_date', 'Open', 'Close']]

    else:  # Yahoo Source
        start_yf = format_date_for_yahoo(start)
        end_yf = format_date_for_yahoo(end)
        try:
            # 明确 auto_adjust=True 减少列名混乱
            df = yf.download(symbol, start=start_yf, end=end_yf, interval="1d", progress=False, auto_adjust=True)
        except Exception as e:
            print("Yahoo报错:", e)
            return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        # 处理新版本 yfinance 可能返回的 MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            # 如果第一层是 Price, Ticker 之类的，取第二层真实的 OHLC
            # 如果第二层是空的，取第一层
            df.columns = [col[1] if col[1] != '' else col[0] for col in df.columns]
        
        df = df.reset_index()
        
        # 统一列名映射
        rename_map = {
            "Date": "trade_date",
            "date": "trade_date",
            "Open": "Open",
            "Close": "Close"
        }
        df.rename(columns=rename_map, inplace=True)

        # 检查关键列是否存在
        if "trade_date" not in df.columns or "Open" not in df.columns or "Close" not in df.columns:
            print("解析后的列名异常:", df.columns.tolist())
            return pd.DataFrame()

        # 确保日期格式正确
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.tz_localize(None)
        
        return df[['trade_date', 'Open', 'Close']]
