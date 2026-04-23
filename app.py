import streamlit as st
from core.data import get_data
from core.strategy import run_strategy
from utils.plot import plot_equity

# 页面配置
st.set_page_config(page_title="完美预测系统", layout="wide")
st.title("📊 完美预测交易分析系统")

# 🚀 缓存函数：同一参数 1 小时内不重复请求网络，防止被 Yahoo 限流
@st.cache_data(ttl=3600)
def fetch_data_cached(symbol, start, end, token):
    return get_data(symbol, start, end, token)

# =========================
# 侧边栏参数区
# =========================
st.sidebar.header("⚙️ 参数设置")

symbol = st.sidebar.text_input("资产代码", "BTC-USD")
start = st.sidebar.text_input("开始日期", "20240101")
end = st.sidebar.text_input("结束日期", "20241231")
freq = st.sidebar.selectbox("时间粒度", ["Day", "Month", "Year"])
fee = st.sidebar.slider("单边手续费 (%)", 0.0, 1.0, 0.1) / 100

# 🛡️ 安全获取 Token 逻辑
# 优先看 Advanced Settings 里的 Secrets，没有则显示输入框
if "token" in st.secrets:
    token = st.secrets["token"]
else:
    token = st.sidebar.text_input("Tushare Token (非必填)", type="password")

run_button = st.sidebar.button("🚀 运行分析")

# =========================
# 主逻辑区
# =========================
if run_button:
    # 简单的非空校验
    if not symbol:
        st.warning("请输入资产代码")
        st.stop()

    with st.spinner("📡 正在抓取并解析数据..."):
        # 调用缓存的获取函数
        df = fetch_data_cached(symbol, start, end, token)

        if df is None or df.empty:
            st.error(f"❌ 无法获取 '{symbol}' 的数据。请检查代码是否正确，或尝试清理缓存后重试。")
            # 提供一个清理缓存的按钮
            if st.button("清理应用缓存"):
                st.cache_data.clear()
        else:
            st.success(f"✅ 成功获取 {len(df)} 条交易记录")

            st.info("⚙️ 正在通过完美预测算法计算收益...")
            result = run_strategy(df, fee, freq)

            # --- 结果展示 ---
            st.subheader("📈 核心绩效指标")
            c1, c2, c3 = st.columns(3)
            
            bh_final = result['bh_cum'].iloc[-1]
            strat_final = result['strategy_cum'].iloc[-1]
            
            c1.metric("买入持有总收益", f"{bh_final:.2f}x")
            c2.metric("完美预测总收益", f"{strat_final:.2e}x") # 收益过大时用科学计数法
            c3.metric("超越倍数", f"{(strat_final/bh_final):.1f}x")

            # --- 绘图 ---
            st.pyplot(plot_equity(result))

            # --- 数据表格 (适配 2026 新语法) ---
            with st.expander("📂 查看详细回测表格"):
                st.dataframe(result, width="stretch")
