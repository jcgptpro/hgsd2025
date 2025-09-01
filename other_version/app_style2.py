
import os
import io
import random
import string
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from PIL import Image, ImageDraw, ImageFont
# ==== Theme & CSS (Tech / Project style) ====
import altair as alt

def _hg_dark_theme():
    return {
        "background":"#0B1220",
        "view":{"strokeOpacity":0},
        "axis":{"labelColor":"#A3B3D3","titleColor":"#A3B3D3","gridColor":"#27324a"},
        "legend":{"labelColor":"#A3B3D3","titleColor":"#A3B3D3"},
        "title":{"color":"#E5E7EB"},
        "range":{"category":["#3B82F6","#06B6D4","#22C55E","#F59E0B","#EF4444","#A855F7"]}
    }

def apply_theme_and_css():
    try:
        alt.themes.register('hg_dark', _hg_dark_theme)
        alt.themes.enable('hg_dark')
    except Exception:
        pass
    # Global CSS (sidebar spacing, neon indicators, dark inputs, primary buttons)
    st.markdown("""
    <style>
    main[data-testid="stAppViewContainer"] { 
      background: radial-gradient(1200px 600px at 10% -10%, rgba(59,130,246,0.10), transparent 60%),
                  radial-gradient(1000px 500px at 90% 10%, rgba(124,58,237,0.08), transparent 60%),
                  #0B1220;
    }
    .block-container { padding-top: 1.2rem; }
    /* Sidebar buttons: left align, tight spacing, neon bar for active */
    section[data-testid="stSidebar"] .stButton>button {
      width:100%; text-align:left!important; background:transparent!important;
      color:#E5E7EB; border:0!important; padding:6px 8px!important; box-shadow:none!important;
    }
    section[data-testid="stSidebar"] .stButton>button:hover { background:rgba(59,130,246,.06)!important; }
    section[data-testid="stSidebar"] .stButton>button:before{
      content:""; position:absolute; left:0; top:6px; bottom:6px; width:3px;
      background: linear-gradient(#3B82F6,#06B6D4); opacity:0; border-radius:2px;
    }
    section[data-testid="stSidebar"] .stButton>button:has(span:contains("👉")):before { opacity:1; }
    /* Inputs dark */
    input, textarea, select {
      background:#0F172A !important; border:1px solid #1F2A44 !important; color:#E5E7EB !important;
    }
    input:focus, textarea:focus, select:focus {
      border-color:#3B82F6 !important; box-shadow:0 0 0 2px rgba(59,130,246,.35) !important;
    }
    /* Primary buttons */
    button[kind="primary"], .stButton>button[kind="primary"] {
      background: linear-gradient(90deg,#2563EB,#06B6D4) !important; border:0!important; color:white!important;
    }
    /* Sticky summary card */
    .hg-sticky { position: fixed; right: 18px; top: 92px; width: 320px; 
      background: rgba(15,23,42,0.75); border:1px solid #1F2A44; border-radius:14px; padding:12px 14px;
      backdrop-filter: blur(6px); z-index: 9999; color:#E5E7EB;
      box-shadow: 0 8px 24px rgba(0,0,0,.35);
    }
    .hg-sticky h4 { margin:0 0 8px 0; font-weight:600; font-size:16px; }
    .hg-kpi { display:flex; gap:12px; flex-wrap:wrap; }
    .hg-kpi .item { flex:1 1 45%; background:rgba(59,130,246,.06); border:1px solid #1F2A44; border-radius:10px; padding:8px; }
    .hg-kpi .label { font-size:12px; color:#A3B3D3; }
    .hg-kpi .val { font-size:16px; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

def render_fixed_summary(which="m1"):
    # Pull from session_state and compute summary quickly
    ss = st.session_state
    html = ""
    if which == "m1":
        try:
            days = (ss.get("m11_end") - ss.get("m11_start")).days + 1
            days = max(days,1)
        except Exception:
            days = 1
        mix = ss.get("channel_mix", {})
        DAY_RATE = {"FB_動態":28000,"IG_限時":24000,"Google_搜尋":32000,"YouTube_展示":18000}
        quote = int(sum((DAY_RATE.get(k,20000)*(v/100)) for k,v in mix.items()) * days)
        kpi =  ss.get("m11_budget",0)
        html = f'''
        <div class="hg-sticky">
          <h4>專案摘要</h4>
          <div class="hg-kpi">
            <div class="item"><div class="label">檔期天數</div><div class="val">{days}</div></div>
            <div class="item"><div class="label">預估報價</div><div class="val">{quote:,}</div></div>
            <div class="item"><div class="label">預算 (TWD)</div><div class="val">{kpi:,}</div></div>
            <div class="item"><div class="label">已選渠道</div><div class="val">{len(mix)}</div></div>
          </div>
        </div>
        '''
    elif which == "m2":
        tas = ss.get("selected_ta", [])
        sizes = ss.get("selected_ta_sizes", {})
        total = sum(sizes.get(t,0) for t in tas)
        html = f'''
        <div class="hg-sticky">
          <h4>TA 摘要</h4>
          <div class="hg-kpi">
            <div class="item"><div class="label">已選 TA</div><div class="val">{len(tas)}</div></div>
            <div class="item"><div class="label">合計人數(估)</div><div class="val">{total:,}</div></div>
          </div>
        </div>
        '''
    elif which == "m3":
        weights = ss.get("m31_weights") or {}
        html = f'''
        <div class="hg-sticky">
          <h4>渠道配比摘要</h4>
          <div class="hg-kpi">
            <div class="item"><div class="label">選用渠道數</div><div class="val">{len(weights)}</div></div>
            <div class="item"><div class="label">合計(%)</div><div class="val">{sum(weights.values())}</div></div>
          </div>
        </div>
        '''
    if html:
        st.markdown(html, unsafe_allow_html=True)
# ==== End Theme & CSS ====

import altair as alt

APP_NAME = "Happy Go CRM+"
SLOGAN = "我們最懂您的客戶與幫助您成長。"

# ------------------------ State & Utils ------------------------

def init_state():
    ss = st.session_state
    ss.setdefault("authed", False)
    ss.setdefault("user_email", "")
    ss.setdefault("company", "Demo Company")
    ss.setdefault("member_tier", "免費會員")
    ss.setdefault("current_page", "📝 提案目標與報價")
    ss.setdefault("order_code", None)
    ss.setdefault("remarketing_tag", False)
    ss.setdefault("survey_sent", False)
    ss.setdefault("channel_mix", {"FB_動態":35, "IG_限時":25, "Google_搜尋":25, "YouTube_展示":15})
    ss.setdefault("persona_df", None)            # 原始 Persona DataFrame
    ss.setdefault("selected_ta", [])             # 被圈選的 TA 名稱
    ss.setdefault("selected_ta_sizes", {})       # {TA: size}
    ss.setdefault("insight_from_upload", None)   # 1-3 上傳的名單分析結果
    # AI panels
    ss.setdefault("show_ai_m11", False)          # 1-1 AI 討論
    ss.setdefault("chat_m11", [])                # 1-1 對話紀錄
    ss.setdefault("show_ai_m12", False)          # 1-2 AI 討論
    ss.setdefault("chat_m12", [])
    # TA 頁：展開更多
    ss.setdefault("m2_expand_more", False)
    # M3 渠道模板（8 渠道，依目標帶預設）
    ss.setdefault("m3_channel_weights", None)    # {"FB":..,"Google":..,...}

def gen_order_code():
    ts = datetime.now().strftime("%Y%m%d")
    suf = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORDER-{ts}-{suf}"

def try_load_persona_default():
    p = os.path.join(".", "Persona_虛擬消費者_202508.xlsx")
    if os.path.exists(p):
        try:
            df = pd.read_excel(p, engine="openpyxl")
            return df
        except Exception:
            return None
    return None

def ensure_persona_loaded():
    ss = st.session_state
    if ss.get("persona_df") is None:
        df = try_load_persona_default()
        if df is not None:
            ss["persona_df"] = df
        else:
            # fallback sample
            ss["persona_df"] = pd.DataFrame({
                "Persona":["年輕都會女性","注重健康上班族","有毛孩家庭","健身重訓者","理性比價族","追劇社交族","品味居家族","通勤族","潮流美妝迷","銀髮熟齡族"],
                "規模":[180000,220000,130000,90000,160000,140000,80000,150000,110000,70000],
                "痛點":["時間不夠","健康+時間管理","用品選擇多","訓練效率","價格敏感","資訊過載","質感與收納","移動時間長","妝容持久度","操作便利"],
                "推薦版位":["IG/FB","Google/FB","FB/IG","IG/YouTube","Google/FB","FB","IG/FB","APP/Push","IG/EDM","EDM/LINE"],
                "關鍵字":["美妝 輕奢 新品","保健 營養 上班族","寵物 飼料 清潔","健身 補劑 重訓","比價 折扣 促銷","口碑 社群 推薦","家居 風格 收納","通勤 便利 小巧","底妝 持妝 防水","簡單 大字 清楚"]
            })

def sidebar_brand():
    # 移除 Logo，只顯示產品名稱與 slogan、公司/會員資訊
    ss = st.session_state
    st.sidebar.markdown(f"### {APP_NAME}")
    st.sidebar.caption(SLOGAN)
    st.sidebar.write(f"**{ss.get('company','')}** · {ss.get('member_tier','')}")
    st.sidebar.divider()
    # 注入 CSS：去邊框、透明、超緊湊、左對齊
    st.sidebar.markdown("""
        <style>
        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            text-align: left !important;
            background: transparent !important;
            color: inherit;
            border: 0 !important;
            padding: 3px 6px !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(0,0,0,0.05) !important;
        }
        </style>
    """, unsafe_allow_html=True)

NAV = [
    "📝 提案目標與報價",
    "🎯 TA 預測與圈選",
    "🧩 渠道與文案製作",
    "📊 成效與顧客洞察",
    "🤝 會員忠誠與再行銷",
    "📚 產業與市場洞察",
    "💳 Order / Billing",
    "👤 Account",
]

def set_query_page(name):
    st.query_params["page"] = name

def get_query_page():
    qp = st.query_params
    return qp["page"] if "page" in qp else None

def nav_button(label, active=False, key=None):
    display = f"👉 {label}" if active else label
    if st.sidebar.button(display, key=key, use_container_width=True):
        if not active:
            st.session_state["current_page"] = label
            set_query_page(label)
            st.rerun()
    # 更緊湊的間距（3px）
    st.sidebar.markdown("<div style='height:3px'></div>", unsafe_allow_html=True)

def global_sidebar_nav():
    sidebar_brand()

    current = st.session_state.get("current_page", NAV[0])
    qp = get_query_page()
    if qp and qp in NAV and qp != current:
        st.session_state["current_page"] = qp
        current = qp

    for i, label in enumerate(NAV):
        nav_button(label, active=(label==current), key=f"nav_{i}")

    st.sidebar.divider()
    if st.sidebar.button("🚪 logout", key="btn_logout"):
        st.session_state.clear()
        st.rerun()

def page_header(title, extra_tag=None):
    st.markdown(f"## {title}")
    crumbs = f"{APP_NAME} / {title}"
    if extra_tag:
        st.write(f":blue[{extra_tag}]  |  {crumbs}")
    else:
        st.caption(crumbs)

# ---------- Helper: KPI & Pricing (簡化估算 for M1) ----------

UNIT_CTR = {"FB_動態":1.2, "IG_限時":1.6, "Google_搜尋":2.2, "YouTube_展示":0.9}
UNIT_CPA = {"FB_動態":130, "IG_限時":140, "Google_搜尋":110, "YouTube_展示":160}

# 媒體每日報價（示意，TWD）
DAY_RATE = {
    "FB_動態": 28000,
    "IG_限時": 24000,
    "Google_搜尋": 32000,
    "YouTube_展示": 18000,
}

def estimate_by_mix(budget, mix):
    if not mix or sum(mix.values()) == 0:
        return {"CTR":0,"CPA":0,"轉換":0,"ROAS":0,"成本":0}
    w = {k:v/sum(mix.values()) for k,v in mix.items()}
    ctr = sum(UNIT_CTR.get(k,1.0)*w[k] for k in w)
    cpa = sum(UNIT_CPA.get(k,150)*w[k] for k in w)
    cost = budget
    conv = int(max(cost/cpa, 0))
    roas = round((conv*300)/cost, 2) if cost>0 else 0
    return {"CTR":round(ctr,2), "CPA":round(cpa,2), "轉換":conv, "ROAS":roas, "成本":cost}

def quote_by_days_and_mix(days, mix, day_rate=DAY_RATE):
    if not mix or sum(mix.values()) == 0:
        return 0, {}
    breakdown = {}
    for ch, pct in mix.items():
        r = day_rate.get(ch, 20000)
        breakdown[ch] = round(days * r * (pct/100))
    return int(sum(breakdown.values())), breakdown

# ---------- GOAL-based channel templates (for M3) ----------

CHANNELS_8 = ["FB","Google","Line","SMS","EDM","APP廣告","APP任務","APP Push"]

GOAL_TEMPLATES = {
    "曝光": {"FB":25,"Google":25,"APP廣告":20,"APP Push":10,"Line":10,"EDM":5,"SMS":3,"APP任務":2},
    "名單": {"Google":30,"FB":25,"EDM":15,"Line":10,"SMS":10,"APP任務":5,"APP Push":3,"APP廣告":2},
    "購買": {"Google":35,"FB":20,"EDM":15,"Line":10,"APP Push":8,"SMS":5,"APP廣告":5,"APP任務":2},
}

def init_m3_channels_from_goal(goal):
    weights = GOAL_TEMPLATES.get(goal, GOAL_TEMPLATES["曝光"]).copy()
    st.session_state["m3_channel_weights"] = weights

# ---------- Auth ----------

def page_login():
    st.title(APP_NAME)
    st.caption(SLOGAN)
    with st.form("login"):
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        c1, c2, c3 = st.columns([1,1,2])
        with c1: sub = st.form_submit_button("登入", use_container_width=True)
        with c2: sso = st.form_submit_button("使用 SSO 登入", use_container_width=True)
        st.caption("忘記密碼")
        if sub or sso:
            if email.strip():
                st.session_state["authed"] = True
                st.session_state["user_email"] = email.strip()
                st.session_state["current_page"] = NAV[0]
                set_query_page(NAV[0])
                st.success("登入成功，前往「提案目標與報價」")
                st.rerun()
            else:
                st.error("請輸入 Email")

# ---------- Module 1：提案目標與報價 ----------

def _orig_m1_page():
    page_header("提案目標與報價", extra_tag=(f"追蹤代碼 {st.session_state['order_code']}" if st.session_state.get("order_code") else None))
    tabs = st.tabs(["媒體提案","市調提案","Shopper 分析","客製分析"])

    # ---- Tab 1-1 媒體提案 ----
    with tabs[0]:
        st.subheader("蒐集需求")
        with st.expander("輸入引導", expanded=True):
            col1, col2 = st.columns(2)
            brand = col1.text_input("品牌名稱", key="m11_brand")
            industry = col2.selectbox("產業", ["保健","運動/健身","寵物","家電","FMCG","美妝","其他"], key="m11_industry")
            goal = col1.selectbox("行銷目標", ["曝光","名單","購買"], key="m11_goal")
            budget = col2.number_input("預算（TWD）", min_value=0, step=10000, value=200000, key="m11_budget")
            start_d = col1.date_input("檔期（開始）", value=date.today(), key="m11_start")
            end_d = col2.date_input("檔期（結束）", value=date.today() + timedelta(days=13), key="m11_end")
            forbidden = st.text_input("禁語/語氣（選填）", placeholder="例如：無療效宣稱、避免醫療用語…", key="m11_forbid")

        # AI 討論（避免 modal，相容）
        if st.button("與 AI 討論提案", key="m11_ai_btn"):
            st.session_state["show_ai_m11"] = True

        if st.session_state.get("show_ai_m11"):
            st.markdown("### 🤖 AI 對話（媒體提案）")
            with st.container():
                st.caption("描述你的產品、受眾與目標，AI 會建議渠道配比與預估成效。")
                for role, msg in st.session_state["chat_m11"]:
                    with st.chat_message(role):
                        st.markdown(msg)
                prompt = st.chat_input("輸入你的問題或補充…", key="m11_chat_input")
                if prompt:
                    st.session_state["chat_m11"].append(("user", prompt))
                    ai = f"根據你的目標「{st.session_state.get('m11_goal','')}」與產業「{st.session_state.get('m11_industry','')}」，建議：Google_搜尋 35%、FB_動態 30%、IG_限時 20%、YouTube_展示 15%。預估 CTR 約 2.1%、CPA 約 120、ROAS 3.2。"
                    st.session_state["chat_m11"].append(("assistant", ai))
                    with st.chat_message("assistant"):
                        st.markdown(ai)
                    st.session_state["channel_mix"] = {"Google_搜尋":35,"FB_動態":30,"IG_限時":20,"YouTube_展示":15}
                if st.button("關閉對話", key="m11_ai_close"):
                    st.session_state["show_ai_m11"] = False
                    st.rerun()

        st.divider()
        st.subheader("渠道配比（可調整，將連動報價）")
        mix = st.session_state.get("channel_mix", {"FB_動態":35,"IG_限時":25,"Google_搜尋":25,"YouTube_展示":15})
        cols = st.columns(4)
        keys = list(mix.keys())
        for i,k in enumerate(keys):
            mix[k] = cols[i].slider(k, 0, 100, int(mix[k]), 5, key=f"m11_mix_{k}")
        total = sum(mix.values())
        if total != 100:
            st.warning(f"目前合計：{total}%（建議調整為 100%）")
        st.session_state["channel_mix"] = mix

        # ---- 新：預估報價（連動 檔期天數 × 渠道配比） ----
        days = (st.session_state.get("m11_end") - st.session_state.get("m11_start")).days + 1
        days = max(days, 1)
        quote, quote_breakdown = quote_by_days_and_mix(days, mix)
        st.subheader("提案摘要 / 報價與成效（自動連動）")
        cA, cB, cC = st.columns(3)
        cA.metric("檔期天數", days)
        cB.metric("預估報價 (TWD)", f"{quote:,}")
        # 成效估算沿用既有 budget（視為客戶預算）
        est = estimate_by_mix(st.session_state.get("m11_budget", 0), mix)
        cC.metric("預估 CTR(%)", est["CTR"])
        cA.metric("預估 CPA", est["CPA"])
        cB.metric("預估 轉換", est["轉換"])
        cC.metric("預估 ROAS", est["ROAS"])
        with st.expander("查看報價明細"):
            st.write(pd.DataFrame({"渠道": list(quote_breakdown.keys()), "金額(TWD)": list(quote_breakdown.values())}))

        if st.button("生成正式委刊單（含追蹤代碼）", key="m11_gen_io"):
            st.session_state["order_code"] = gen_order_code()
            st.success(f"已產生正式委刊單，追蹤代碼：{st.session_state['order_code']}")
            # 初始化 M3 渠道模板（依目標）
            init_m3_channels_from_goal(st.session_state.get("m11_goal","曝光"))

    # ---- Tab 1-2 市調提案 ----
    with tabs[1]:
        st.subheader("市調提案設定")
        n = st.number_input("目標樣本數", min_value=50, step=50, value=200, key="m12_n")
        qtype = st.selectbox("問卷型式", ["封閉題為主","開放題為主","混合題（建議）"], key="m12_qtype")
        target = st.text_input("受訪條件（年齡／地區／興趣等）", key="m12_target")

        base_cost = 25
        if "開放" in qtype:
            unit = int(base_cost * 2.2)
            eta = "10–14 天"
        elif "混合" in qtype:
            unit = int(base_cost * 1.6)
            eta = "7–10 天"
        else:
            unit = base_cost
            eta = "5–7 天"
        est_cost = unit * n
        st.info(f"預估報價：約 TWD {est_cost:,}；預估時程：{eta}（示意，依題目複雜度調整）")

        if st.button("與 AI 討論市調設計", key="m12_ai_btn"):
            st.session_state["show_ai_m12"] = True
        if st.session_state.get("show_ai_m12"):
            st.markdown("### 🤖 AI 對話（市調提案）")
            with st.container():
                st.caption("說明你要驗證的假設、族群與預算，AI 會建議題型與樣本結構。")
                for role, msg in st.session_state["chat_m12"]:
                    with st.chat_message(role):
                        st.markdown(msg)
                prompt = st.chat_input("輸入你的需求…", key="m12_chat_input")
                if prompt:
                    st.session_state["chat_m12"].append(("user", prompt))
                    ai = f"建議樣本數 {n}、{qtype}，可觀測品牌知名度、價格敏感度、使用障礙。時程 {eta}。"
                    st.session_state["chat_m12"].append(("assistant", ai))
                    with st.chat_message("assistant"):
                        st.markdown(ai)
                if st.button("關閉對話", key="m12_ai_close"):
                    st.session_state["show_ai_m12"] = False
                    st.rerun()

        # 僅能生成委刊單，不再提供跳 TA 的按鈕
        if st.button("生成正式委刊單（含追蹤代碼）", key="m12_gen_io"):
            st.session_state["order_code"] = gen_order_code()
            st.success(f"已產生正式委刊單，追蹤代碼：{st.session_state['order_code']}")

    # ---- Tab 1-3 Shopper 分析 ----
    with tabs[2]:
        st.subheader("上傳名單進行 Shopper 分析")
        uploaded = st.file_uploader("上傳名單（CSV 或 XLSX）", type=["csv","xlsx"], key="m13_upload")
        if uploaded:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded, engine="openpyxl")
                st.dataframe(df.head())
                st.write(f"筆數：{len(df)}")
                if "region" in df.columns or "地區" in df.columns:
                    col = "region" if "region" in df.columns else "地區"
                    st.bar_chart(df[col].value_counts())
                st.session_state["insight_from_upload"] = {
                    "rows": len(df),
                    "top_region": df["region"].value_counts().idxmax() if "region" in df.columns else None,
                    "note": "基於上傳名單的初步輪廓，已導入 產業與市場洞察 > 提案分析。"
                }
                st.success("分析完成，已同步到 產業與市場洞察。")
            except Exception as e:
                st.error(f"讀取失敗：{e}")

        st.divider()
        st.caption("個資使用宣告：上傳之名單僅用於本次分析，不會儲存於伺服器。您可隨時要求刪除。")

    # ---- Tab 1-4 客製分析 ----
    with tabs[3]:
        st.subheader("客製分析需求")
        st.text_area("請描述你的特殊題目與想要的交付", height=120, key="m14_desc")
        st.multiselect("資料來源", ["會員/銷售","投放數據","市調回收","OpenData","其他"], key="m14_srcs")
        st.button("送出需求", key="m14_submit")

# ---------- Module 2：TA 預測與圈選（AI 推薦 + 展開更多；需追蹤代碼） ----------

def normalize_persona(df):
    cols = df.columns.tolist()
    def pick(cands, default=None):
        for c in cands:
            if c in cols: return c
        return default
    name_col = pick(["Persona","名稱","人物","族群","TA","人設"], cols[0] if cols else None)
    size_col = pick(["規模","人數","樣本數","估計規模"], None)
    pain_col = pick(["痛點","需求","阻礙"], None)
    kw_col   = pick(["關鍵字","關鍵詞","Keywords"], None)
    slot_col = pick(["推薦版位","偏好版位","版位","渠道偏好"], None)
    att_col  = pick(["態度","傾向","Attitude"], None)

    items = []
    for _,row in df.iterrows():
        name = str(row.get(name_col,"Persona"))
        size = int(row.get(size_col, 100000) if pd.notna(row.get(size_col, None)) else 100000)
        pain = str(row.get(pain_col,"價格敏感/怕踩雷"))
        kw   = str(row.get(kw_col,""))
        slot = str(row.get(slot_col,"FB/IG/Google"))
        att  = str(row.get(att_col,"價格敏感, 品牌忠誠中等, 追求體驗"))
        items.append({"name":name,"size":size,"pain":pain,"keywords":kw,"slots":slot,"attitudes":att})
    return items

def pick_ai_recommended_personas(items, industry, goal, k=5):
    # 簡易規則：依關鍵字與痛點/態度對應產業與目標做打分，取前 k
    scores = []
    ind_kw = str(industry or "").lower()
    goal_kw = str(goal or "").lower()
    for it in items:
        s = 0
        text = (it["name"]+" "+it["pain"]+" "+it["keywords"]+" "+it["slots"]+" "+it["attitudes"]).lower()
        # 產業關聯度
        if "美妝" in ind_kw or "beauty" in ind_kw:
            s += ("妝" in text) * 2 + ("女性" in text) * 1
        if "家電" in ind_kw or "appliance" in ind_kw:
            s += ("理性" in text) * 2 + ("比價" in text) * 2 + ("功能" in text) * 1
        if "保健" in ind_kw:
            s += ("健康" in text) * 2 + ("上班" in text) * 1
        if "寵物" in ind_kw:
            s += ("寵物" in text) * 3
        if "運動" in ind_kw or "健身" in ind_kw:
            s += ("健身" in text) * 3 + ("效率" in text)*1
        if "fmcg" in ind_kw:
            s += ("比價" in text) * 1 + ("促銷" in text)*1
        # 目標關聯度
        if "曝光" in goal_kw:
            s += ("社群" in text) + ("口碑" in text) + ("年輕" in text)
        if "名單" in goal_kw:
            s += ("搜尋" in text) + ("關鍵字" in text) + ("line" in text) + ("edm" in text)
        if "購買" in goal_kw:
            s += ("比價" in text) + ("功能" in text) + ("評價" in text)
        # 規模微調
        s += min(it["size"]/200000, 1.0)
        scores.append((s, it))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scores[:k]]

def _orig_m2_page():
    page_header("TA 預測與圈選", extra_tag=(f"追蹤代碼 {st.session_state['order_code']}" if st.session_state.get("order_code") else None))

    # 追蹤代碼 gating
    if not st.session_state.get("order_code"):
        st.info("要開始圈選 TA，請先在「提案目標與報價」或「市調提案」生成正式委刊單（追蹤代碼）。")
        return

    ensure_persona_loaded()
    items = normalize_persona(st.session_state["persona_df"])
    industry = st.session_state.get("m11_industry","其他")
    goal = st.session_state.get("m11_goal","曝光")

    st.markdown("#### AI 推薦的 5 個 Persona")
    recs = pick_ai_recommended_personas(items, industry, goal, k=5)

    selections = set(st.session_state.get("selected_ta", []))
    sizes_map = dict(st.session_state.get("selected_ta_sizes", {}))

    cols = st.columns(5)
    for i, it in enumerate(recs):
        with cols[i % 5]:
            st.markdown(f"**{it['name']}** · 規模：約 {it['size']:,}")
            st.caption(f"痛點：{it['pain']}")
            checked = st.checkbox("選擇", key=f"m2_rec_{i}", value=(it['name'] in selections))
            if checked:
                selections.add(it['name']); sizes_map[it['name']] = it['size']
            else:
                selections.discard(it['name']); sizes_map.pop(it['name'], None)

    st.toggle("展開更多 TA", key="m2_expand_more")
    if st.session_state.get("m2_expand_more"):
        st.markdown("#### 更多 Persona")
        grid = st.columns(3)
        for idx, it in enumerate(items):
            # 跳過已在推薦中出現的
            if any(it['name']==r['name'] for r in recs): 
                continue
            with grid[idx % 3]:
                st.markdown(f"**{it['name']}**  · 規模：約 {it['size']:,}")
                st.caption(f"痛點：{it['pain']}")
                checked = st.checkbox("選擇此 TA", key=f"m2_all_{idx}", value=(it['name'] in selections))
                if checked:
                    selections.add(it['name']); sizes_map[it['name']] = it['size']
                else:
                    if it['name'] in selections:
                        selections.discard(it['name']); sizes_map.pop(it['name'], None)

    # 已選合計
    total_size = sum(sizes_map.get(name, 0) for name in selections)
    st.info(f"已選 TA：**{len(selections)}** 個｜合計人數：約 **{total_size:,}** 人（示意）")
    st.session_state["selected_ta"] = list(selections)
    st.session_state["selected_ta_sizes"] = sizes_map

    c1, c2 = st.columns(2)
    if c1.button("鎖定這些 TA", key="m2_lock"):
        st.success("已鎖定 TA，前往『渠道與文案製作』")
        st.session_state["current_page"] = "🧩 渠道與文案製作"
        set_query_page("🧩 渠道與文案製作")
        st.rerun()
    if c2.button("返回提案", key="m2_back"):
        st.session_state["current_page"] = "📝 提案目標與報價"
        set_query_page("📝 提案目標與報價")
        st.rerun()

# ---------- Module 3：渠道與文案製作 ----------

def build_image_prompt(ta_name, frame_type, channel):
    persona_hint = f"{ta_name}，關鍵痛點：價格敏感/怕踩雷；情緒訴求與功能利益兼具"
    frame_hint = {
        "A 情境寫實":"生活化場景，人物自然互動，品牌 Logo 右下",
        "B 產品特寫":"產品細節特寫，乾淨背景，Logo 右上",
        "C 前後對比":"before/after 效果對比，強調改善幅度，Logo 置中偏下"
    }[frame_type]
    prompt = (
        f"{frame_type}／{channel} 視覺：以 {persona_hint}；"
        f"畫面描述：{frame_hint}；"
        "構圖留白可置入 12–16 字標題與 6–10 字 CTA；尺寸輸出 1:1、4:5、16:9。"
    )
    return prompt

def channel_defaults_from_goal():
    goal = st.session_state.get("m11_goal","曝光")
    if st.session_state.get("m3_channel_weights") is None:
        init_m3_channels_from_goal(goal)
    return st.session_state["m3_channel_weights"]

CHANNELS_8 = ["FB","Google","Line","SMS","EDM","APP廣告","APP任務","APP Push"]

def _orig_m3_page():
    page_header("渠道與文案製作")
    tabs = st.tabs(["媒體渠道＋文案／圖片","市調出題"])

    with tabs[0]:
        st.subheader("選擇渠道與版位（依提案目標預設配比，可調整）")
        weights = channel_defaults_from_goal().copy()
        # 選擇哪些渠道（預設：權重 >=5 的打勾）
        default_selected = [ch for ch,w in weights.items() if w>=5]
        selected = st.multiselect("選擇渠道", CHANNELS_8, default=default_selected, key="m31_channels")

        # 每個選中的渠道配比（%）
        st.markdown("##### 渠道配比（%）")
        cols = st.columns(4)
        new_weights = {}
        for idx, ch in enumerate(CHANNELS_8):
            if ch in selected:
                with cols[idx % 4]:
                    new_weights[ch] = st.number_input(ch, min_value=0, max_value=100, value=int(weights.get(ch,0)), step=1, key=f"m31_w_{ch}")
        total = sum(new_weights.values()) if new_weights else 0
        if total != 100 and total != 0:
            st.warning(f"目前合計：{total}%（建議調整為 100%）")
        st.session_state["m31_weights"] = new_weights

        st.divider()
        st.subheader("為每個 TA × 渠道生成 3 則文案")
        ta_list = st.session_state.get("selected_ta", [])
        if not ta_list:
            st.info("請先在『TA 預測與圈選』鎖定 TA。")
        else:
            channel_tones = {
                "FB": ("口語社群感", ["快來看","大家都在討論","私訊小編"]),
                "Google": ("關鍵詞導向", ["了解方案","立即比較","線上試算"]),
                "Line": ("熟客貼近", ["加入好友","領取折扣","客服協助"]),
                "SMS": ("極簡直白", ["領取連結","限時序號","回覆Y領取"]),
                "EDM": ("資訊完整", ["查看詳情","領取優惠","立即註冊"]),
                "APP廣告": ("行動即時", ["立即開啟","點我體驗","立刻查看"]),
                "APP任務": ("互動任務", ["完成任務拿點數","解鎖獎勵","參與挑戰"]),
                "APP Push": ("緊湊提醒", ["點我領券","限時開搶","回來看看"]),
            }
            for ta in ta_list:
                st.markdown(f"**{ta}**")
                for ch in selected:
                    tone, ctas = channel_tones.get(ch, ("一般語氣", ["立即了解","加入購物車","馬上逛逛"]))
                    pains = ["時間不夠","不知道選哪款","價格敏感","怕踩雷","需要快速見效"]
                    hooks = ["限時優惠","熱銷口碑","專屬會員禮","新品搶先","加碼回饋"]
                    st.caption(f"— {ch} 建議語氣：{tone}")
                    for i in range(3):
                        txt = f"{hooks[i%len(hooks)]}！{ta}常見『{pains[i%len(pains)]}』，{ctas[i%len(ctas)]}。"
                        st.write(f"{i+1}. {txt}")
                st.write("---")

        st.subheader("圖片版型：AI 生成素材的 Prompt 建議")
        frame_type = st.selectbox("選擇圖片版型", ["A 情境寫實","B 產品特寫","C 前後對比"], key="m31_frame")
        prompt_all = []
        for ta in ta_list:
            for ch in (selected or ["FB"]):
                prompt_all.append(build_image_prompt(ta, frame_type, ch))
        if prompt_all:
            st.code("\n\n".join(prompt_all), language="text")
            if st.button("請 AI 生圖（示意）", key="m31_gen_image"):
                text = " ".join(prompt_all[:3])
                img = Image.new("RGB", (1024, 640), (245,245,245))
                d = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 24)
                except:
                    font = ImageFont.load_default()
                d.text((24,20), "AI 生圖占位（可接外部圖像 API）", fill=(60,60,60), font=font)
                y=60
                for line in text[:300].split("／"):
                    d.text((24,y), line.strip(), fill=(0,0,0), font=font)
                    y+=28
                buf=io.BytesIO(); img.save(buf, format="PNG")
                st.image(buf.getvalue(), caption="AI 生成占位圖（Demo）")
        else:
            st.info("請先選 TA 與渠道，再產生 Prompt。")

    with tabs[1]:
        st.subheader("虛擬消費者態度（連結選定 TA）")
        ensure_persona_loaded()
        df = st.session_state.get("persona_df")
        if df is not None and len(st.session_state.get("selected_ta", []))>0:
            items = normalize_persona(df)
            pick = [it for it in items if it["name"] in st.session_state["selected_ta"]]
            tags = [it["attitudes"] for it in pick]
            st.write("預估填寫傾向（示意）：")
            st.write("、".join(tags) if tags else "（無）")
        else:
            st.info("尚未載入 Persona 或尚未選定 TA。")

        st.divider()
        st.write("問卷結構")
        st.json({
            "封閉題": ["Q1: 您的年齡？", "Q2: 您過去3個月是否購買過本類商品？"],
            "開放題": ["Q3: 影響您購買的最重要原因是？"],
            "情境題(虛擬消費者Q&A)": ["Q4: 如果看到『新品搶先』的貼文，您會？"]
        })
        st.write("題目編輯器（示意）")
        st.text_area("編輯題幹/選項/跳題規則", height=120, key="m32_editor")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("AI 產生題組", key="m32_ai_gen")
        c2.button("匯入樣板", key="m32_import")
        c3.button("預覽", key="m32_preview")
        # 新增：請虛擬消費者作答（模擬）
        if c4.button("請虛擬消費者作答", key="m32_simulate"):
            # 產生模擬回覆（示意）
            rng = np.random.default_rng(99)
            n = 120
            ta_list = st.session_state.get("selected_ta", [])
            tas = ta_list or ["年輕都會女性","理性比價族"]
            ages = rng.choice(["18–24","25–34","35–44","45–54","55+"], size=n, p=[0.22,0.33,0.25,0.14,0.06])
            bought = rng.choice(["是","否"], size=n, p=[0.46,0.54])
            persona = rng.choice(tas, size=n)
            free_text = [f"{p}：價格要合理、{rng.choice(['耐用','口碑','設計'])}很重要" for p in persona]
            df_ans = pd.DataFrame({"Persona":persona,"Q1_年齡":ages,"Q2_是否購買":bought,"Q3_開放回答":free_text})
            st.success("已產生 120 份模擬作答（示意）。")
            st.dataframe(df_ans.head())
            st.download_button("下載 simulated_answers.csv", data=df_ans.to_csv(index=False), file_name="simulated_answers.csv")
        st.caption("＊示意資料，日後可替換為真 AI 生成或 Panel 收集。")

# ---------- Module 4：成效與顧客洞察（新增 多張分析圖 + 顧客洞察 子頁） ----------

def random_kpi():
    rng = np.random.default_rng(42)
    return {
        "曝光": int(rng.integers(200000, 800000)),
        "點擊": int(rng.integers(5000, 30000)),
        "CTR": round(float(rng.uniform(0.5, 3.5)), 2),
        "轉換": int(rng.integers(200, 2000)),
        "CPA": round(float(rng.uniform(50, 300)), 2),
        "ROAS": round(float(rng.uniform(1.2, 6.0)), 2),
    }

def matrix_sample():
    rows = []
    channels = CHANNELS_8
    copies = [f"文案_{i}" for i in range(1, 6)]
    frames = ["A_情境", "B_特寫", "C_對比"]
    rng = np.random.default_rng(7)
    for ch in channels:
        for cp in copies:
            for fr in frames:
                ctr = float(rng.uniform(0.3, 4.0))
                cpa = float(rng.uniform(40, 350))
                rows.append([ch, cp, fr, round(ctr, 2), round(cpa, 2)])
    return pd.DataFrame(rows, columns=["版位/平台", "文案", "圖片版型", "CTR(%)", "CPA"])

def gen_daily_perf(days=14, channels=CHANNELS_8, seed=123):
    rng = np.random.default_rng(seed)
    start = date.today() - timedelta(days=days-1)
    rows = []
    # 基於模板權重生成每日數據
    weights = st.session_state.get("m31_weights") or {ch: 100/len(channels) for ch in channels}
    wsum = sum(weights.values()) or 1
    for i in range(days):
        d = start + timedelta(days=i)
        for ch in channels:
            w = weights.get(ch, 0)/wsum
            imp = int(rng.integers(10000, 60000) * (0.7 + 0.6*w))
            clk = int(imp * rng.uniform(0.005, 0.03) * (0.7 + 0.6*w))
            conv = int(clk * rng.uniform(0.02, 0.2))
            spend = int(conv * rng.uniform(80, 220))
            rows.append([d, ch, imp, clk, conv, spend])
    return pd.DataFrame(rows, columns=["date","channel","impressions","clicks","conversions","spend"])

def gen_customer_insight_data(seed=123):
    rng = np.random.default_rng(seed)
    total = int(rng.integers(1500, 6000))
    trend = round(float(rng.uniform(-8, 18)), 1)
    gender = pd.Series(rng.multinomial(total, [0.48, 0.50, 0.02]), index=["女性","男性","其他"])
    age_bins = ["18–24","25–34","35–44","45–54","55+"]
    age = pd.Series(rng.multinomial(total, [0.18,0.32,0.28,0.15,0.07]), index=age_bins)
    cities = ["台北市","新北市","桃園市","台中市","高雄市","台南市","新竹市","基隆市","宜蘭縣","花蓮縣"]
    city_probs = np.array([0.22,0.20,0.12,0.15,0.12,0.07,0.04,0.03,0.03,0.02])
    cities_ser = pd.Series(rng.multinomial(total, city_probs/city_probs.sum()), index=cities)
    categories = ["3C","休閒旅遊娛樂","居家生活","服飾配件","保健","美容保養","食品餐飲","家電","婦幼親子","運動健身","寵物"]
    cats_ser = pd.Series(rng.multinomial(total, rng.dirichlet(np.ones(len(categories)))), index=categories).sort_values(ascending=False)
    channels = ["遠東百貨","SOGO","7-11","全家","康是美","屈臣氏","家樂福","全聯","momo","PChome","蝦皮","誠品","大潤發","Costco","OK Mart","萊爾富","愛買","小北百貨"]
    ch_ser = pd.Series(rng.multinomial(total, rng.dirichlet(np.ones(len(channels)))), index=channels).sort_values(ascending=False)
    return total, trend, gender, age, cities_ser, cats_ser, ch_ser

def m4_page():
    page_header("成效與顧客洞察")
    tabs = st.tabs(["媒體投放成效與洞察","顧客洞察","市調回收成效"])
    # --- 投放成效 ---
    with tabs[0]:
        st.subheader("KPI 摘要")
        kpi = random_kpi()
        c1,c2,c3 = st.columns(3)
        c1.metric("曝光", f"{kpi['曝光']:,}")
        c2.metric("點擊", f"{kpi['點擊']:,}")
        c3.metric("CTR(%)", kpi['CTR'])
        c1.metric("轉換", f"{kpi['轉換']:,}")
        c2.metric("CPA", kpi['CPA'])
        c3.metric("ROAS", kpi['ROAS'])

        st.subheader("投放趨勢與表現（示意）")
        perf = gen_daily_perf(days=14)
        # 日趨勢
        st.markdown("**日趨勢：曝光 / 點擊 / 轉換**")
        trend = perf.groupby("date")[["impressions","clicks","conversions"]].sum()
        st.line_chart(trend)

        # 渠道堆疊（花費）
        st.markdown("**每日花費 × 渠道（堆疊）**")
        pivot_spend = perf.pivot_table(index="date", columns="channel", values="spend", aggfunc="sum").fillna(0)
        st.area_chart(pivot_spend)

        # 各渠道 CTR / CPA
        st.markdown("**各渠道 CTR / CPA**")
        sum_ch = perf.groupby("channel").sum(numeric_only=True)
        ctr_ch = (sum_ch["clicks"]/sum_ch["impressions"]).fillna(0)*100
        cpa_ch = (sum_ch["spend"]/sum_ch["conversions"]).replace([np.inf, np.nan], 0)
        st.bar_chart(pd.DataFrame({"CTR(%)":ctr_ch.sort_values(ascending=False)}))
        st.bar_chart(pd.DataFrame({"CPA":cpa_ch.sort_values()}))

        # 文案×版型熱點圖（用 matrix_sample）
        st.markdown("**文案 × 圖片版型 熱點圖（CTR，示意）**")
        mat = matrix_sample()
        heat = mat.pivot_table(index="文案", columns="圖片版型", values="CTR(%)", aggfunc="mean")
                # 嘗試使用背景漸層（需要 matplotlib），否則退回 Altair 熱點圖
        try:
            import matplotlib  # noqa: F401
            st.dataframe(heat.style.background_gradient(cmap="YlOrRd"))
        except Exception:
            st.caption("提示：未安裝 matplotlib，改以 Altair 呈現熱點圖。")
            heat_long = heat.reset_index().melt(id_vars=["文案"], var_name="圖片版型", value_name="CTR")
            chart = alt.Chart(heat_long).mark_rect().encode(
                x=alt.X("圖片版型:O"),
                y=alt.Y("文案:O"),
                color=alt.Color("CTR:Q"),
                tooltip=["文案","圖片版型","CTR"]
            )
            st.altair_chart(chart, use_container_width=True)

        st.subheader("AI 洞察（示意）")
        st.write("- 亮點：Google CTR 持續上升；Line/SMS 對回流轉換有幫助。")
        st.write("- 風險：FB 頻率過高、CPC 上升，需更換鉤子。")
        st.write("- 建議：提高 Google 10% 預算；APP Push 改用 A 情境；FB 更換文案。")
        if st.button("加入再行銷提案", key="m41_add_re"):
            st.session_state["remarketing_tag"] = True
            st.session_state["current_page"] = "📝 提案目標與報價"
            set_query_page("📝 提案目標與報價")
            st.rerun()

    # --- 顧客洞察 ---
    with tabs[1]:
        st.subheader("成交顧客概況（示意）")
        total, trend, gender, age, cities_ser, cats_ser, ch_ser = gen_customer_insight_data()
        c1,c2 = st.columns(2)
        c1.metric("成交顧客數（近期）", f"{total:,}", f"{'+' if trend>=0 else ''}{trend}%")
        c2.metric("Top 城市", cities_ser.sort_values(ascending=False).index[0])
        st.markdown("##### 性別分佈")
        st.bar_chart(gender)
        st.markdown("##### 年齡層分佈")
        st.bar_chart(age)
        st.markdown("##### 居住地 Top 5")
        st.bar_chart(cities_ser.sort_values(ascending=False).head(5))
        st.markdown("##### 交易部類排行（Top 10）")
        st.bar_chart(cats_ser.head(10))
        st.markdown("##### 交易通路排行（Top 10）")
        st.bar_chart(ch_ser.head(10))

    # --- 市調回收成效 ---
    with tabs[2]:
        st.subheader("市調回收成效（示意）")
        if st.session_state.get("survey_sent"):
            st.success("問卷已回收 186 份")
        st.write("封閉題統計")
        st.bar_chart(pd.DataFrame({"選項A":[68],"選項B":[82],"選項C":[36]}))
        st.write("開放題自動編碼（可下載微調）")
        codes = pd.DataFrame({
            "原始回覆": ["價格要合理","穿起來要舒適","希望有無鋼圈款"],
            "自動標籤": ["價格敏感","舒適度","無鋼圈"]
        })
        st.dataframe(codes)
        st.download_button("下載 open_coding.csv", data=codes.to_csv(index=False), file_name="open_coding.csv", key="m42_dl_coding")
        st.write("AI 態度標籤雲：正面 63%｜中立 28%｜負面 9%")

# ---------- Module 5：忠誠與再行銷（各子頁加 AI 洞察建議） ----------

def loyalty_ai_tips(industry, ta_list, topic):
    base = ["以 Line+EDM 建立固定節奏", "針對高價值客戶推出 VIP 體驗", "APP Push 搭配限時碼提升回流"]
    if industry in ["美妝","美容保養"]: base.append("新品試色/前後對比加強內容口碑")
    if industry in ["家電"]: base.append("延長保固與規格對比，加強理性主張")
    if industry in ["保健"]: base.append("定期購提醒與專家背書教育內容")
    if topic=="新客": base.append("Lookalike + Google 關鍵詞長尾抓新客")
    if topic=="沉睡": base.append("回流限定禮/回饋金，避免過度頻次")
    if ta_list: base.append(f"已選 TA：{', '.join(ta_list[:3])}… 進行差異化 CTA 與頻率控制")
    return base[:5]

def m5_page():
    page_header("會員忠誠與再行銷")
    tabs = st.tabs(["NES 總覽","新客預測與放大","沉睡客預測與喚醒","既有客鞏固計畫"])
    industry = st.session_state.get("m11_industry","其他")
    ta_list = st.session_state.get("selected_ta", [])

    with tabs[0]:
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("新客（近30天）", "3,420", "+12%")
        with c2: st.metric("沉睡客（近90天）", "1,180", "-6%")
        with c3: st.metric("活躍會員", "26,540", "+3%")
        st.markdown("##### AI 洞察建議")
        for tip in loyalty_ai_tips(industry, ta_list, topic="NES"):
            st.write(f"- {tip}")

    with tabs[1]:
        st.write("候選名單（示意）")
        df = pd.DataFrame({"顧客ID":[f"C{i:05d}" for i in range(1,11)],"相似度":[round(random.random()*0.25+0.7,2) for _ in range(10)]})
        st.dataframe(df)
        st.markdown("##### AI 洞察建議")
        for tip in loyalty_ai_tips(industry, ta_list, topic="新客"):
            st.write(f"- {tip}")
        if st.button("生成新提案（新客放大）", key="m52_new"):
            st.session_state["current_page"] = "📝 提案目標與報價"
            set_query_page("📝 提案目標與報價")
            st.rerun()

    with tabs[2]:
        st.write("沉睡風險名單（示意）")
        df = pd.DataFrame({"顧客ID":[f"Z{i:05d}" for i in range(1,11)],"流失機率":[round(random.random()*0.3+0.6,2) for _ in range(10)]})
        st.dataframe(df)
        st.markdown("##### AI 洞察建議")
        for tip in loyalty_ai_tips(industry, ta_list, topic="沉睡"):
            st.write(f"- {tip}")
        if st.button("生成新提案（喚醒計畫）", key="m53_new"):
            st.session_state["current_page"] = "📝 提案目標與報價"
            set_query_page("📝 提案目標與報價")
            st.rerun()

    with tabs[3]:
        st.write("忠誠活動建議（示意）")
        st.markdown("- 會員日：每月第 1 週末雙倍點數\n- 新品試用組合包\n- 高價值客戶 VIP 線下體驗")
        st.write("採納追蹤")
        st.checkbox("已採納：會員日雙倍點數", key="m54_ck1")
        st.checkbox("已採納：新品試用組合包", key="m54_ck2")
        st.markdown("##### AI 洞察建議")
        for tip in loyalty_ai_tips(industry, ta_list, topic="鞏固"):
            st.write(f"- {tip}")
        if st.button("生成新提案（鞏固計畫）", key="m54_new"):
            st.session_state["current_page"] = "📝 提案目標與報價"
            set_query_page("📝 提案目標與報價")
            st.rerun()

# ---------- Module 6：產業與市場洞察（各子頁加 AI 洞察建議） ----------

def ai_insights_for_industry(industry, ta_list):
    # 規則生成 3-5 條建議
    tips = []
    if industry in ["美妝","保養","美容保養"]:
        tips += ["以IG/FB短句口碑與前後對比呈現","鎖定25–34女性，強調妝容持久與敏感肌安心"]
    if industry in ["家電","家用","家電產品"] or "家電" in industry:
        tips += ["Google 搜尋＋比較頁素材，凸顯規格與保固","EDM 長版規格表＋舊換新方案"]
    if industry in ["保健","營養","健康"]:
        tips += ["Line 與 EDM 深度教育內容，搭配醫師背書","APP Push 促發『定期購』與試用包"]
    if not tips:
        tips = ["以 Google×FB 建立基本漏斗；EDM/Line 作名單養熟","APP Push 催化回流，加上 SMS 限時碼"]
    if ta_list:
        tips.append(f"已選 TA：{', '.join(ta_list[:3])}…，建議製作專屬痛點鉤子與不同 CTA A/B。")
    return tips[:5]

def m6_page():
    page_header("產業與市場洞察")
    tabs = st.tabs(["重點客戶／主力客群","提案分析／會員健檢","OpenData 報告"])
    industry = st.session_state.get("m11_industry","其他")
    ta_list = st.session_state.get("selected_ta", [])

    with tabs[0]:
        st.write("主力客群與趨勢（示意）")
        st.dataframe(pd.DataFrame({
            "客群":["年輕都會女性","有毛孩家庭","健身重訓者"],
            "近季消費力變化(%)":[+8,-3,+5]
        }))
        st.markdown("##### AI 洞察建議")
        for tip in ai_insights_for_industry(industry, ta_list):
            st.write(f"- {tip}")

    with tabs[1]:
        st.write("會員健檢（五面向燈號）")
        df = pd.DataFrame({"面向":["情感","功能","價格","會員","體驗"],"燈號":["🟢","🟡","🟢","🟡","🟢"]})
        st.dataframe(df)
        ins = st.session_state.get("insight_from_upload")
        if ins:
            st.success(f"已載入 1-3 分析：共 {ins['rows']} 筆；Top 區域：{ins['top_region']}")
            st.caption(ins["note"])
        st.markdown("##### AI 洞察建議")
        for tip in ai_insights_for_industry(industry, ta_list):
            st.write(f"- {tip}")

    with tabs[2]:
        st.write("OpenData 區域/產業底稿（示意）")
        st.dataframe(pd.DataFrame({
            "指標":["人口數","批發零售營業額","餐飲營業額","CPI"],
            "值":["2,450,000","+3.1%","+4.2%","+2.3%"]
        }))
        st.markdown("##### AI 洞察建議")
        for tip in ai_insights_for_industry(industry, ta_list):
            st.write(f"- {tip}")

# ---------- Module 7：Order / Billing ----------

def m7_page():
    page_header("Order / Billing", extra_tag=(f"追蹤代碼 {st.session_state['order_code']}" if st.session_state.get("order_code") else None))
    st.subheader("方案與使用量")
    plan = st.selectbox("目前方案", ["Free","Team","Professional","Enterprise"], index=0, key="m7_plan")
    usage = pd.DataFrame({"項目":["AI 對話","市調回收","生成素材"], "本月用量":[42, 186, 12], "額度":[100, 1000, 100]})
    st.dataframe(usage)

    st.subheader("付款方式")
    with st.form("pay_form"):
        name = st.text_input("持卡人", key="m7_card_name")
        card = st.text_input("卡號（只示意）", value="**** **** **** 4242", key="m7_card_no")
        exp = st.text_input("到期", value="12/29", key="m7_card_exp")
        submit = st.form_submit_button("更新付款方式")
        if submit:
            st.success("已更新付款方式（示意）")

    st.subheader("發票/抬頭")
    with st.form("invoice_form"):
        title = st.text_input("抬頭", key="m7_inv_title")
        taxid = st.text_input("統編", key="m7_inv_taxid")
        addr = st.text_area("地址", height=80, key="m7_inv_addr")
        inv_submit = st.form_submit_button("儲存發票資訊")
        if inv_submit:
            st.success("已儲存（示意）")

    st.subheader("歷史帳單")
    bills = pd.DataFrame({
        "月份":["2025-06","2025-05","2025-04"],
        "金額":[3200,3200,0],
        "狀態":["已付款","已付款","Free"],
        "收據":["下載","下載","-"]
    })
    st.dataframe(bills)

# ---------- Module 8：Account（含 會員升級） ----------

def m8_page():
    page_header("Account")
    st.subheader("公司/品牌資料")
    col1,col2 = st.columns([2,3])
    with col2:
        st.text_input("公司/品牌名稱", value=st.session_state.get("company","Demo Company"), key="company")
        st.selectbox("會員等級", ["免費會員","Team","Professional","Enterprise"], key="member_tier")
    st.markdown("---")
    st.subheader("會員升級")
    if st.button("升級會員", key="m8_upgrade_btn"):
        st.session_state["m8_show_upgrade"] = True
    if st.session_state.get("m8_show_upgrade"):
        cols = st.columns(3)
        plans = [
            ("Team","NT$3,200/月","成員 5、AI 對話 1,000、市調回收 5,000"),
            ("Professional","NT$8,900/月","成員 15、AI 對話 5,000、市調回收 20,000"),
            ("Enterprise","洽談","SSO、客製模型、專屬頻寬"),
        ]
        chosen = st.radio("選擇方案", [p[0] for p in plans], horizontal=True, key="m8_pick_plan")
        for i,(name, price, feat) in enumerate(plans):
            with cols[i]:
                st.markdown(f"**{name}**")
                st.caption(price)
                st.write(feat)
        if st.button("確認升級", key="m8_confirm_upgrade"):
            st.session_state["member_tier"] = chosen
            st.success(f"已升級為 {chosen}，請至 Order/Billing 完成付款資訊。")
    st.markdown("---")

    st.subheader("成員與角色/權限")
    members = pd.DataFrame({
        "Email":[st.session_state.get("user_email","you@company.com"),"pm@company.com","it@company.com"],
        "角色":["Admin","Editor","Viewer"]
    })
    st.data_editor(members, num_rows="dynamic", key="m8_members")

    st.subheader("安全設定")
    st.toggle("啟用 2FA", value=False, key="m8_2fa")
    st.text_input("密碼策略（示意）", value="至少 12 碼、含大小寫與數字", key="m8_pwd_policy")

    st.subheader("API 金鑰")
    c1,c2 = st.columns(2)
    with c1:
        st.text_input("OpenAI API Key（示意，不儲存）", type="password", key="m8_openai_key")
    with c2:
        if st.button("重置 API 金鑰", key="m8_reset_key"):
            st.info("已重置（示意）")

# ------------------------ Main ------------------------

# ---- Wrappers to inject sticky summary ----
def m1_page():
    _orig_m1_page()
    try:
        render_fixed_summary("m1")
    except Exception:
        pass

def m2_page():
    _orig_m2_page()
    try:
        render_fixed_summary("m2")
    except Exception:
        pass

def m3_page():
    _orig_m3_page()
    try:
        render_fixed_summary("m3")
    except Exception:
        pass


def main():
    st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")
    apply_theme_and_css()
    init_state()

    if not st.session_state["authed"]:
        page_login()
        return

    global_sidebar_nav()

    page = st.session_state.get("current_page", NAV[0])
    if page.endswith("提案目標與報價"):
        m1_page()
    elif page.endswith("TA 預測與圈選"):
        m2_page()
    elif page.endswith("渠道與文案製作"):
        m3_page()
    elif page.endswith("成效與顧客洞察"):
        m4_page()
    elif page.endswith("會員忠誠與再行銷"):
        m5_page()
    elif page.endswith("產業與市場洞察"):
        m6_page()
    elif page.endswith("Order / Billing"):
        m7_page()
    elif page.endswith("Account"):
        m8_page()
    else:
        m1_page()

if __name__ == "__main__":
    main()

