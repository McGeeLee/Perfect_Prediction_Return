import streamlit as st
from core.data import get_data
from core.strategy import run_strategy
from utils.plot import plot_equity

st.set_page_config(page_title="完美预测系统", layout="wide")
st.title("📊 完美预测交易分析系统")

# 使用 Streamlit 缓存机制：相同的参数在 1 小时内不会重复请求网络
@st.cache_data(ttl=3600)
def fetch_data_cached(symbol, start, end, token):
    return get_data(symbol, start, end, token)

st.sidebar.header("⚙️ 参数设置")
symbol = st.sidebar.text_input("资产代码", "BTC-USD") # 默认改为 BTC 方便测试
start = st.sidebar.text_input("开始日期", "20200101")
end = st.sidebar.text_input("结束日期", "20250101")
freq = st.sidebar.selectbox("时间粒度", ["Year", "Month", "Day"])
fee = st.sidebar.slider("单边手续费 (%)", 0.0, 1.0, 0.1) / 100

# 优先从 Secrets 获取 Token，没有则显示输入框
if "token" in st.secrets:
    token = st.secrets["token"]
else:
    token = st.sidebar.text_input("Tushare Token", type="password")

if st.sidebar.button("运行分析"):
    if not token and not symbol.endswith("-USD"):
        st.warning("请输入 Tushare Token 以获取 A 股数据")
    else:
        with st.spinner("📡 正在获取并分析数据..."):
            df = fetch_data_cached(symbol, start, end, token)

            if df.empty:
                st.error(f"❌ 数据获取失败：请检查代码 '{symbol}' 是否正确，或尝试更换网络（可能被 Yahoo 限流）。")
            else:
                st.success(f"✅ 成功获取 {len(df)} 条数据")
                
                result = run_strategy(df, fee, freq)
                
                # 指标展示
                c1, c2, c3 = st.columns(3)
                final_bh = result['bh_cum'].iloc[-1]
                final_str = result['strategy_cum'].iloc[-1]
                c1.metric("持股不动收益", f"{final_bh:.2f}x")
                c2.metric("完美预测收益", f"{final_str:.2f}x")
                c3.metric("超额倍数", f"{(final_str/final_bh):.1f}x")

                # 图表展示
                st.pyplot(plot_equity(result))
                
                # 数据详情
                with st.expander("查看详细计算数据"):
                    st.dataframe(result, use_container_width=True)
