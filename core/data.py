import tushare as ts
import yfinance as yf
import pandas as pd

def detect_asset(symbol):
    """识别资产类型和数据源"""
    symbol = symbol.upper()
    # ===== Crypto / 全球资产 =====
    if "-USD" in symbol or any(c.isalpha() for c in symbol) and "." not in symbol:
        return "global", "Yahoo"
    # ===== A股 / ETF =====
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        code = symbol.split(".")[0]
        if code.startswith("51"):
            return "etf", "Tushare"
        elif code.startswith(("6", "0", "3")):
            return "stock", "Tushare"
    return "other", "Yahoo"

def format_date_for_yahoo(date_str):
    """日期格式转换 20250101 -> 2025-01-01"""
    if "-" not in date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

def get_data(symbol, start, end, token=None):
    asset_type, source = detect_asset(symbol)
    print(f"识别: {asset_type} | 数据源: {source}")

    # =========================
    # Tushare 数据源
    # =========================
    if source == "Tushare":
        if not token: return pd.DataFrame()
        ts.set_token(token)
        pro = ts.pro_api()
        try:
            if asset_type == "stock":
                df = pro.daily(ts_code=symbol, start_date=start, end_date=end)
            elif asset_type == "etf":
                df = pro.fund_daily(ts_code=symbol, start_date=start, end_date=end)
            else: return pd.DataFrame()
            
            if df is None or df.empty: return pd.DataFrame()
            df = df.sort_values("trade_date")
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.rename(columns={'open': 'Open', 'close': 'Close'}, inplace=True)
            return df[['trade_date', 'Open', 'Close']]
        except Exception as e:
            print(f"Tushare Error: {e}")
            return pd.DataFrame()

    # =========================
    # Yahoo 数据源 (BTC-USD 等)
    # =========================
    else:
        start_yf = format_date_for_yahoo(start)
        end_yf = format_date_for_yahoo(end)
        try:
            # 下载原始数据
            df = yf.download(symbol, start=start_yf, end=end_yf, interval="1d", progress=False)
            
            if df is None or df.empty:
                return pd.DataFrame()

            # 🚀 核心修复：处理你调试发现的 MultiIndex [('Close', 'BTC-USD')...]
            if isinstance(df.columns, pd.MultiIndex):
                # 你的调试显示 Level 0 是 ['Close', 'High', 'Low', 'Open', 'Volume']
                # 我们强制保留 Level 0 丢弃 Level 1
                df.columns = df.columns.get_level_values(0)
            
            # 将索引（Date）转为列
            df = df.reset_index()
            
            # 清洗列名，防止空格干扰
            df.columns = [str(c).strip() for c in df.columns]

            # 统一列名映射
            rename_map = {
                "Date": "trade_date",
                "date": "trade_date",
                "Open": "Open",
                "Close": "Close"
            }
            df.rename(columns=rename_map, inplace=True)

            # 最终检查关键列
            if "trade_date" in df.columns and "Open" in df.columns and "Close" in df.columns:
                # 移除时区信息并转换日期
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.tz_localize(None)
                # 显式转换 Open/Close 为浮点数，防止某些版本返回 Object 导致计算报错
                df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
                df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                
                return df[['trade_date', 'Open', 'Close']].dropna()
            else:
                print(f"清洗后列名不匹配: {df.columns.tolist()}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Yahoo 逻辑执行报错: {e}")
            return pd.DataFrame()
