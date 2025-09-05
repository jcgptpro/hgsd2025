import os
import io
import base64
import random
import string
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageFont

APP_NAME = "HAPPYGO CRM+"
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
    ss.setdefault("persona_df", None)       # 原始 Persona DataFrame
    ss.setdefault("selected_ta", [])        # 被圈選的 TA 名稱
    ss.setdefault("insight_from_upload", None)  # 1-3 上傳的名單分析結果
    ss.setdefault("logo_bytes", None)       # 自訂 Logo bytes
    # AI Panel states
    ss.setdefault("show_ai_m11", False)     # 1-1 AI 討論
    ss.setdefault("chat_m11", [])           # 1-1 對話紀錄
    ss.setdefault("show_ai_m12", False)     # 1-2 AI 討論
    ss.setdefault("chat_m12", [])

def gen_order_code():
    ts = datetime.now().strftime("%Y%m%d")
    suf = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORDER-{ts}-{suf}"

def load_default_logo():
    # 讀取程式目錄 logo_1_20220331026.png
    p = os.path.join(".", "logo_1_20220331026.png")
    if os.path.exists(p):
        with open(p, "rb") as f:
            return f.read()
    return None

def try_load_persona_default():
    # 讀取程式目錄 Persona_虛擬消費者_202508.xlsx
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

def sidebar_brand():
    ss = st.session_state
    st.sidebar.markdown(" ")
    logo_bytes = ss.get("logo_bytes") or load_default_logo()
    cols = st.sidebar.columns([1,6])
    with cols[0]:
        if logo_bytes:
            st.image(logo_bytes, use_column_width=True)
        else:
            st.write("🎯")
    with cols[1]:
        st.sidebar.markdown(f"### {APP_NAME}")
        st.sidebar.caption(SLOGAN)
        st.sidebar.write(f"**{ss.get('company','')}** · {ss.get('member_tier','')}")
    st.sidebar.divider()

NAV = [
    "📝 提案目標與報價",
    "🎯 TA 預測與圈選",
    "🧩 渠道與文案製作",
    "📊 成效與顧客洞察",
    "🤝 會員忠誠與再行銷",
    "📚 產業報告",
    "💳 Order / Billing",
    "👤 Account",
]

def set_query_page(name):
    st.query_params["page"] = name

def get_query_page():
    qp = st.query_params
    return qp["page"] if "page" in qp else None

def nav_button(label, active=False, key=None):
    # 單列按鈕導覽（無 radio 圓點），加大間距
    if active:
        st.sidebar.button(f"👉 {label}", key=key, use_container_width=True, disabled=True)
    else:
        if st.sidebar.button(label, key=key, use_container_width=True):
            st.session_state["current_page"] = label
            set_query_page(label)
            st.rerun()
    st.sidebar.markdown("&nbsp;", unsafe_allow_html=True)  # 間距

def global_sidebar_nav():
    sidebar_brand()

    current = st.session_state.get("current_page", NAV[0])
    qp = get_query_page()
    if qp and qp in NAV and qp != current:
        st.session_state["current_page"] = qp
        current = qp

    # 用按鈕替代 radio（無圓點），每個都加 key，並拉開間距
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

# ---------- Helper: KPI & Pricing (簡化估算) ----------

UNIT_CTR = {"FB_動態":1.2, "IG_限時":1.6, "Google_搜尋":2.2, "YouTube_展示":0.9}
UNIT_CPA = {"FB_動態":130, "IG_限時":140, "Google_搜尋":110, "YouTube_展示":160}

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

def m1_page():
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
            end_d = col2.date_input("檔期（結束）", value=date.today(), key="m11_end")
            forbidden = st.text_input("禁語/語氣（選填）", placeholder="例如：無療效宣稱、避免醫療用語…", key="m11_forbid")

        # AI 討論：頁面內聊天面板（避免 st.modal 相容性問題）
        if st.button("與 AI 討論提案", key="m11_ai_btn"):
            st.session_state["show_ai_m11"] = True

        if st.session_state.get("show_ai_m11"):
            st.markdown("### 🤖 AI 對話（媒體提案）")
            with st.container():  # 不使用 border 參數以提高相容性
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

        est = estimate_by_mix(st.session_state.get("m11_budget", 0), mix)
        st.subheader("提案摘要 / 報價（自動連動）")
        cA, cB, cC = st.columns(3)
        with cA: st.metric("預估 CTR(%)", est["CTR"])
        with cB: st.metric("預估 CPA", est["CPA"])
        with cC: st.metric("預估 轉換", est["轉換"])
        cA.metric("預估 ROAS", est["ROAS"])
        cB.metric("預估 成本", f"{est['成本']:,}")
        st.caption("＊估算公式可依實務係數調整")

        if st.button("生成正式委刊單（含追蹤代碼）", key="m11_gen_io"):
            st.session_state["order_code"] = gen_order_code()
            st.success(f"已產生正式委刊單，追蹤代碼：{st.session_state['order_code']}")

    # ---- Tab 1-2 市調提案 ----
    with tabs[1]:
        st.subheader("市調提案設定")
        n = st.number_input("目標樣本數", min_value=50, step=50, value=200, key="m12_n")
        qtype = st.selectbox("問卷型式", ["封閉題為主","開放題為主","混合題（建議）"], key="m12_qtype")
        target = st.text_input("受訪條件（年齡／地區／興趣等）", key="m12_target")
        est_cost = n * 25
        st.info(f"預估成本：約 TWD {est_cost:,}；預估時程：5–7 天")

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
                    ai = f"建議樣本數 {n}、混合題型（封閉70%/開放30%），可觀測品牌知名度、價格敏感度、使用障礙。預估完成 5–7 天。"
                    st.session_state["chat_m12"].append(("assistant", ai))
                    with st.chat_message("assistant"):
                        st.markdown(ai)
                if st.button("關閉對話", key="m12_ai_close"):
                    st.session_state["show_ai_m12"] = False
                    st.rerun()

        c1, c2 = st.columns(2)
        if c1.button("生成正式委刊單（含追蹤代碼）", key="m12_gen_io"):
            st.session_state["order_code"] = gen_order_code()
            st.success(f"已產生正式委刊單，追蹤代碼：{st.session_state['order_code']}")
        if c2.button("前往 TA 預測與圈選", key="m12_to_m2"):
            st.session_state["current_page"] = "🎯 TA 預測與圈選"
            set_query_page("🎯 TA 預測與圈選")
            st.rerun()

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
                    st.bar_chart(df[col].value_counts(), key="m13_region_chart")
                st.session_state["insight_from_upload"] = {
                    "rows": len(df),
                    "top_region": df["region"].value_counts().idxmax() if "region" in df.columns else None,
                    "note": "基於上傳名單的初步輪廓，已導入 6-2 提案分析。"
                }
                st.success("分析完成，已同步到 6-2 提案分析。")
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

# ---------- Module 2：TA 預測與圈選（用 Persona 檔） ----------

def normalize_persona(df):
    cols = df.columns.tolist()
    def pick(cands, default=None):
        for c in cands:
            if c in cols:
                return c
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

def m2_page():
    page_header("TA 預測與圈選", extra_tag=(f"追蹤代碼 {st.session_state['order_code']}" if st.session_state.get("order_code") else None))

    ensure_persona_loaded()

    st.write("Persona 來源：")
    uploaded = st.file_uploader("上傳 Persona Excel（若未自動載入）", type=["xlsx"], key="m2_upload_persona")
    if uploaded:
        df = pd.read_excel(uploaded, engine="openpyxl")
        st.session_state["persona_df"] = df
    elif st.session_state.get("persona_df") is None:
        st.info("尚未載入 Persona 檔，將使用系統示例")
        st.session_state["persona_df"] = pd.DataFrame({
            "Persona":["年輕都會女性","注重健康上班族","有毛孩家庭","健身重訓者","理性比價族"],
            "規模":[180000,220000,130000,90000,160000],
            "痛點":["時間不夠","健康+時間管理","用品選擇多","訓練效率","價格敏感"],
            "推薦版位":["IG/FB","Google/FB","FB/IG","IG/YouTube","Google/FB"]
        })

    items = normalize_persona(st.session_state["persona_df"])

    cols = st.columns(3)
    selections = set(st.session_state.get("selected_ta", []))
    for idx, it in enumerate(items):
        with cols[idx % 3]:
            st.markdown(f"**{it['name']}**  · 規模：約 {it['size']:,}")
            st.caption(f"痛點：{it['pain']}")
            st.caption(f"偏好版位：{it['slots']}")
            st.caption(f"關鍵字：{it['keywords'] or '—'}")
            st.caption(f"態度：{it['attitudes']}")
            checked = st.checkbox("選擇此 TA", key=f"m2_ta_{idx}", value=(it['name'] in selections))
            if checked:
                selections.add(it['name'])
            else:
                selections.discard(it['name'])
    st.session_state["selected_ta"] = list(selections)

    st.divider()
    grow = st.slider("放大人數（%）", 0, 100, 10, step=5, key="m2_grow")
    exclude = st.text_input("排除條件（如已購買、特定區域）", key="m2_exclude")

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

def generate_placeholder_image(prompt_text):
    img = Image.new("RGB", (1024, 640), (245, 245, 245))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    wrapped = []
    line = ""
    for w in prompt_text.split():
        if len(line + " " + w) < 40:
            line = (line + " " + w).strip()
        else:
            wrapped.append(line)
            line = w
    wrapped.append(line)
    y = 40
    d.text((40, 20), "AI 生圖占位（可接外部圖像 API）", fill=(60,60,60), font=font)
    for ln in wrapped[:12]:
        d.text((40, y), ln, fill=(0,0,0), font=font)
        y += 28
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def m3_page():
    page_header("渠道與文案製作")
    tabs = st.tabs(["媒體渠道＋文案／圖片","市調出題"])

    with tabs[0]:
        st.subheader("選擇渠道與版位")
        channels = st.multiselect("選擇渠道", ["FB_動態","IG_限時","Google_搜尋","YouTube_展示","LINE_好友"], key="m31_channels")

        st.divider()
        st.subheader("文案建議（每個 TA 五則）")
        ta_list = st.session_state.get("selected_ta", [])
        if not ta_list:
            st.info("請先在『TA 預測與圈選』鎖定 TA。")
        for ta in ta_list:
            st.markdown(f"**{ta}**")
            hooks = ["限時優惠","熱銷口碑","專屬會員禮","新品搶先","買一送一"]
            pains = ["時間不夠","不知道選哪款","價格敏感","怕踩雷","需要快速見效"]
            ctas = ["立即了解","加入購物車","領取優惠","免費試用","馬上逛逛"]
            for i in range(5):
                st.write(f"{i+1}. {random.choice(hooks)}！{ta}的你，{random.choice(pains)}？{random.choice(ctas)}。")
            st.write("---")

        st.subheader("圖片版型：AI 生成素材的 Prompt 建議")
        frame_type = st.selectbox("選擇圖片版型", ["A 情境寫實","B 產品特寫","C 前後對比"], key="m31_frame")
        prompt_all = []
        for ta in ta_list:
            for ch in (st.session_state.get("m31_channels") or ["FB_動態"]):
                prompt_all.append(build_image_prompt(ta, frame_type, ch))
        if prompt_all:
            st.code("\n\n".join(prompt_all), language="text")
            st.download_button("下載 prompts.txt", data=("\n\n".join(prompt_all)).encode("utf-8"),
                               file_name="prompts.txt", key="m31_dl_prompts")
            if st.button("請 AI 生圖（示意）", key="m31_gen_image"):
                img_bytes = generate_placeholder_image(" ".join(prompt_all[:3]))
                st.image(img_bytes, caption="AI 生成占位圖（Demo）")
                st.download_button("下載生成圖片", data=img_bytes, file_name="ai_image.png", key="m31_dl_img")
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
        if c4.button("發送", key="m32_send"):
            st.session_state["survey_sent"] = True
            st.session_state["current_page"] = "📊 成效與顧客洞察"
            set_query_page("📊 成效與顧客洞察")
            st.success("已發送問卷，前往成效頁")
            st.rerun()

# ---------- Module 4：成效與顧客洞察 ----------

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
    channels = ["FB_動態", "IG_限時", "Google_搜尋", "YouTube_展示", "LINE_好友"]
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

def m4_page():
    page_header("成效與顧客洞察")
    tabs = st.tabs(["媒體投放成效與洞察","市調回收成效"])
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
        st.subheader("圖片版型 × 文案 × 版位 矩陣")
        df = matrix_sample()
        st.dataframe(df)
        st.subheader("AI 洞察（示意）")
        st.write("- 亮點：產品特寫（B）在 Google_搜尋 CTR 最高；IG_限時對年輕都會女性表現佳。")
        st.write("- 風險：FB_動態出現疲勞（頻率過高、CPC 上升）。")
        st.write("- 建議：提高 Google_搜尋 10% 預算；IG_限時改用 A 情境；FB_動態更換文案鉤子。")
        c1, c2 = st.columns(2)
        if c1.button("加入再行銷提案", key="m41_add_re"):
            st.session_state["remarketing_tag"] = True
            st.session_state["current_page"] = "📝 提案目標與報價"
            set_query_page("📝 提案目標與報價")
            st.rerun()
        st.download_button("下載週報 CSV", data=df.to_csv(index=False), file_name="performance.csv",
                           mime="text/csv", key="m41_dl_report")

    with tabs[1]:
        st.subheader("市調回收成效（示意）")
        if st.session_state.get("survey_sent"):
            st.success("問卷已回收 186 份")
        st.write("封閉題統計")
        st.bar_chart(pd.DataFrame({"選項A":[68],"選項B":[82],"選項C":[36]}), key="m42_chart")
        st.write("開放題自動編碼（可下載微調）")
        codes = pd.DataFrame({
            "原始回覆": ["價格要合理","穿起來要舒適","希望有無鋼圈款"],
            "自動標籤": ["價格敏感","舒適度","無鋼圈"]
        })
        st.dataframe(codes)
        st.download_button("下載 open_coding.csv", data=codes.to_csv(index=False), file_name="open_coding.csv", key="m42_dl_coding")
        st.write("AI 態度標籤雲：正面 63%｜中立 28%｜負面 9%")

# ---------- Module 5：忠誠與再行銷 ----------

def m5_page():
    page_header("會員忠誠與再行銷")
    tabs = st.tabs(["NES 總覽","新客預測與放大","沉睡客預測與喚醒","既有客鞏固計畫"])
    with tabs[0]:
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("新客（近30天）", "3,420", "+12%")
        with c2: st.metric("沉睡客（近90天）", "1,180", "-6%")
        with c3: st.metric("活躍會員", "26,540", "+3%")
    with tabs[1]:
        st.write("候選名單（示意）")
        df = pd.DataFrame({"顧客ID":[f"C{i:05d}" for i in range(1,11)],"相似度":[round(random.random()*0.25+0.7,2) for _ in range(10)]})
        st.dataframe(df)
        if st.button("生成新提案（新客放大）", key="m52_new"):
            st.session_state["current_page"] = "📝 提案目標與報價"
            set_query_page("📝 提案目標與報價")
            st.rerun()
    with tabs[2]:
        st.write("沉睡風險名單（示意）")
        df = pd.DataFrame({"顧客ID":[f"Z{i:05d}" for i in range(1,11)],"流失機率":[round(random.random()*0.3+0.6,2) for _ in range(10)]})
        st.dataframe(df)
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
        if st.button("生成新提案（鞏固計畫）", key="m54_new"):
            st.session_state["current_page"] = "📝 提案目標與報價"
            set_query_page("📝 提案目標與報價")
            st.rerun()

# ---------- Module 6：產業報告 ----------

def m6_page():
    page_header("產業報告")
    tabs = st.tabs(["重點客戶／主力客群","提案分析／會員健檢","OpenData 報告"])
    with tabs[0]:
        st.write("主力客群與趨勢（示意）")
        st.dataframe(pd.DataFrame({
            "客群":["年輕都會女性","有毛孩家庭","健身重訓者"],
            "近季消費力變化(%)":[+8,-3,+5]
        }))
        st.download_button("下載 PPT（示意）", data=b"Placeholder PPT bytes", file_name="insight_placeholder.pptx", key="m61_dl_ppt")
    with tabs[1]:
        st.write("會員健檢（五面向燈號）")
        df = pd.DataFrame({"面向":["情感","功能","價格","會員","體驗"],"燈號":["🟢","🟡","🟢","🟡","🟢"]})
        st.dataframe(df)
        ins = st.session_state.get("insight_from_upload")
        if ins:
            st.success(f"已載入 1-3 分析：共 {ins['rows']} 筆；Top 區域：{ins['top_region']}")
            st.caption(ins["note"])
        with st.expander("訂閱定期發送"):
            freq = st.selectbox("頻率", ["每月","每季"], key="m62_freq")
            email = st.text_input("寄送對象 Email", key="m62_email")
            st.button("建立訂閱", key="m62_subscribe")
    with tabs[2]:
        st.write("OpenData 區域/產業底稿（示意）")
        st.dataframe(pd.DataFrame({
            "指標":["人口數","批發零售營業額","餐飲營業額","CPI"],
            "值":["2,450,000","+3.1%","+4.2%","+2.3%"]
        }))

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

# ---------- Module 8：Account ----------

def m8_page():
    page_header("Account")
    st.subheader("公司/品牌資料")
    col1,col2 = st.columns([2,3])
    with col1:
        up = st.file_uploader("上傳 Logo（PNG）", type=["png"], key="m8_logo_upload")
        if up:
            st.session_state["logo_bytes"] = up.read()
            st.success("已更新 Logo（顯示於側欄）")
    with col2:
        st.text_input("公司/品牌名稱", value=st.session_state.get("company","Demo Company"), key="company")
        st.selectbox("會員等級", ["免費會員","Team","Professional","Enterprise"], key="member_tier")

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

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")
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
    elif page.endswith("產業報告"):
        m6_page()
    elif page.endswith("Order / Billing"):
        m7_page()
    elif page.endswith("Account"):
        m8_page()
    else:
        m1_page()

if __name__ == "__main__":
    main()
