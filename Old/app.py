
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import random
import string

APP_NAME = "Happy Go CRM+"
SLOGAN = "我們最懂您的客戶與幫助您成長。"

# ---------- Utilities ----------

def init_state():
    ss = st.session_state
    ss.setdefault("authed", False)
    ss.setdefault("user_email", "")
    ss.setdefault("company", "Demo Company")
    ss.setdefault("member_tier", "免費會員")
    ss.setdefault("current_module", "Module 1｜提案目標與報價")
    ss.setdefault("order_code", None)
    ss.setdefault("ta_locked", False)
    ss.setdefault("ta_clusters", [])
    ss.setdefault("is_remarketing", False)
    ss.setdefault("survey_sent", False)

def gen_order_code():
    ts = datetime.now().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORDER-{ts}-{suffix}"

def kpi_sample():
    rng = np.random.default_rng(42)
    data = {
        "曝光": int(rng.integers(200000, 800000)),
        "點擊": int(rng.integers(5000, 30000)),
        "CTR": round(float(rng.uniform(0.5, 3.5)), 2),
        "轉換": int(rng.integers(200, 2000)),
        "CPA": round(float(rng.uniform(50, 300)), 2),
        "ROAS": round(float(rng.uniform(1.2, 6.0)), 2),
    }
    return data

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
    df = pd.DataFrame(rows, columns=["版位/平台", "文案", "圖片版型", "CTR(%)", "CPA"])
    return df

def copy_suggestions_for_ta(ta_name, n=5):
    hooks = ["限時優惠", "熱銷口碑", "專屬會員禮", "新品搶先", "買一送一", "醫師推薦", "運動必備", "萌寵必囤"]
    pain = ["時間不夠", "不知道選哪款", "價格敏感", "怕踩雷", "需要快速見效"]
    ctas = ["立即了解", "加入購物車", "領取優惠", "免費試用", "馬上逛逛"]
    out = []
    for i in range(n):
        s = f"{random.choice(hooks)}！{ta_name}的你，{random.choice(pain)}？{random.choice(ctas)}。"
        out.append(s)
    return out

def export_csv(df, filename):
    return df.to_csv(index=False).encode("utf-8-sig"), filename

def export_copy_csv(copy_dict):
    rows = []
    for ta, arr in copy_dict.items():
        for i, s in enumerate(arr, 1):
            rows.append([ta, f"文案{i}", s])
    df = pd.DataFrame(rows, columns=["TA", "文案名稱", "內容"])
    return export_csv(df, "copy_suggestions.csv")

def spec_text(channels_selected):
    sizes = "1:1 / 4:5 / 16:9"
    return (
        "圖片版型規格（Wireframe 建議）\\n"
        "- A 情境寫實：標題<=14字、CTA<=8字、Logo 安全區右下；尺寸："+sizes+"\\n"
        "- B 產品特寫：標題<=12字、CTA<=10字、Logo 安全區右上；尺寸："+sizes+"\\n"
        "- C 前後對比：標題<=16字、CTA<=8字、Logo 安全區居中偏下；尺寸："+sizes+"\\n"
        f"\\n本次選擇渠道/版位：{', '.join(channels_selected) if channels_selected else '（尚未選擇）'}\\n"
    ).encode("utf-8")

# ---------- Navigation (top-level) ----------

NAV_OPTIONS = [
    "Module 1｜提案目標與報價",
    "Module 2｜TA 預測與圈選",
    "Module 3｜渠道與文案製作",
    "Module 4｜成效與顧客洞察",
    "Module 5｜會員忠誠與再行銷",
    "Module 6｜產業報告",
]

def global_sidebar():
    # Brand area
    st.sidebar.markdown(f"### {APP_NAME}")
    st.sidebar.caption(SLOGAN)
    st.sidebar.write(f"**{st.session_state.get('company','')}** · {st.session_state.get('member_tier','')}")
    st.sidebar.divider()

    # Main nav (radio). Using a key makes it persist; update state immediately then rerun.
    selected = st.sidebar.radio("功能選單", NAV_OPTIONS, key="nav_selected",
                                index=NAV_OPTIONS.index(st.session_state.get("current_module", NAV_OPTIONS[0])))

    # Disabled placeholders
    st.sidebar.divider()
    st.sidebar.markdown("**帳務與帳戶**")
    st.sidebar.button("7｜Order / Billing（即將推出）", disabled=True)
    st.sidebar.button("8｜Account（即將推出）", disabled=True)

    st.sidebar.divider()
    if st.sidebar.button("9｜logout"):
        st.session_state.clear()
        st.rerun()

    # If changed, update state and rerun immediately so content switches in the same click
    if selected != st.session_state.get("current_module"):
        st.session_state["current_module"] = selected
        st.rerun()

def page_header(title, breadcrumb=None, extra_tag=None):
    st.markdown(f"## {title}")
    crumbs = breadcrumb or f"{APP_NAME} / {title}"
    if extra_tag:
        st.write(f":blue[{extra_tag}]  |  {crumbs}")
    else:
        st.caption(crumbs)

# ---------- Pages ----------

def page_login():
    st.title(APP_NAME)
    st.caption(SLOGAN)
    with st.form("login"):
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            submitted = st.form_submit_button("登入")
        with col2:
            sso = st.form_submit_button("使用 SSO 登入")
        st.caption("忘記密碼")
        if submitted or sso:
            if email.strip():
                st.session_state["authed"] = True
                st.session_state["user_email"] = email.strip()
                st.session_state["current_module"] = NAV_OPTIONS[0]
                st.success("登入成功，前往提案目標與報價")
                st.rerun()
            else:
                st.error("請輸入 Email")

def module1():
    page_header("提案目標與報價")
    tabs = st.tabs(["功能頁面1-1 媒體提案","功能頁面1-2 市調提案","功能頁面1-3 Shopper 分析","功能頁面1-4 客製分析"])
    # 1-1
    with tabs[0]:
        st.subheader("Chatbot（蒐集需求）")
        with st.expander("輸入引導", expanded=True):
            col1, col2 = st.columns(2)
            brand = col1.text_input("品牌名稱")
            industry = col2.selectbox("產業", ["保健","運動/健身","寵物","家電","FMCG","其他"])
            goal = col1.selectbox("行銷目標", ["曝光","名單","購買"])
            budget = col2.number_input("預算（TWD）", min_value=0, step=10000, value=200000)
            period = col1.date_input("檔期（開始）", value=date.today())
            period_end = col2.date_input("檔期（結束）", value=date.today())
            forbidden = st.text_input("禁語/語氣（選填）", placeholder="例如：無療效宣稱、避免醫療用語…")
        st.divider()
        st.subheader("提案摘要 / 報價")
        colA, colB, colC = st.columns(3)
        with colA:
            st.metric("預估 CTR(%)", 1.8, "+0.3")
            st.metric("預估 CPA", "120")
        with colB:
            st.metric("預估 轉換", "980")
            st.metric("預估 ROAS", "3.5")
        with colC:
            st.write("渠道配比（示意）")
            st.dataframe(pd.DataFrame({
                "平台/版位":["FB_動態","IG_限時","Google_搜尋","YouTube_展示"],
                "比例%":[35,25,25,15]
            }))
        col1, col2, col3 = st.columns(3)
        if col1.button("生成正式委刊單"):
            st.success("已產生正式委刊單（範例）")
        if col2.button("產生追蹤代碼"):
            st.session_state["order_code"] = gen_order_code()
            st.success(f"追蹤代碼：{st.session_state['order_code']}")
        col3.button("儲存草稿")
    # 1-2
    with tabs[1]:
        st.subheader("市調提案設定")
        n = st.number_input("目標樣本數", min_value=50, step=50, value=200)
        qtype = st.selectbox("問卷型式", ["封閉題為主","開放題為主","混合題（建議）"])
        est_cost = n * 25
        st.info(f"預估成本：約 TWD {est_cost:,}")
        st.button("生成市調委刊單")
    # 1-3
    with tabs[2]:
        st.subheader("Shopper 分析（示意）")
        st.caption("資料期間")
        col1, col2 = st.columns(2)
        col1.date_input("開始", value=date(date.today().year,1,1))
        col2.date_input("結束", value=date.today())
        st.write("• 會員分級：新客 23%｜活躍 52%｜沉睡 25%")
        st.write("• 跨品類組合：保健x寵物、健身x蛋白粉、家電x清潔耗材")
        if st.button("連到 Module 6：產業報告"):
            st.session_state["current_module"] = "Module 6｜產業報告"
            st.rerun()
    # 1-4
    with tabs[3]:
        st.subheader("客製分析需求")
        st.text_area("請描述你的特殊題目與想要的交付", height=120)
        st.multiselect("資料來源", ["會員/銷售","投放數據","市調回收","OpenData","其他"])
        st.button("送出需求")

def module2():
    oc = st.session_state.get("order_code")
    page_header("TA 預測與圈選", extra_tag=f"追蹤代碼 {oc}" if oc else None)
    if not oc:
        st.warning("尚未產生追蹤代碼，請先到『提案目標與報價』產生。")
        return
    if not st.session_state["ta_clusters"]:
        candidates = [
            ("年輕都會女性", 180000),
            ("注重健康上班族", 220000),
            ("有毛孩家庭", 130000),
            ("健身重訓者", 90000),
            ("理性比價族", 160000),
        ]
        st.session_state["ta_clusters"] = candidates[:random.randint(3,5)]
    cols = st.columns(len(st.session_state["ta_clusters"]))
    for i,(name,size) in enumerate(st.session_state["ta_clusters"]):
        with cols[i]:
            st.markdown(f"**{name}**")
            st.caption(f"規模：約 {size:,}")
            st.write("痛點：時間不夠／怕踩雷／價格敏感")
            st.write("推薦版位：FB 動態、IG 限時、Google 搜尋")
    st.divider()
    with st.expander("微調受眾", expanded=False):
        grow = st.slider("放大人數（%）", 0, 100, 10, step=5)
        exclude = st.text_input("排除條件（如已購買、特定區域）")
        if st.button("套用微調"):
            new = []
            for name,size in st.session_state["ta_clusters"]:
                new.append((name, int(size*(1+grow/100))))
            st.session_state["ta_clusters"] = new
            st.success("已更新受眾規模")
    if st.button("鎖定這些 TA"):
        st.session_state["ta_locked"] = True
        st.session_state["current_module"] = "Module 3｜渠道與文案製作"
        st.success("已鎖定 TA，前往『渠道與文案製作』")
        st.rerun()

def module3():
    page_header("渠道與文案製作")
    tabs = st.tabs(["功能頁面3-1 渠道推薦＋文案/圖片","功能頁面3-2 市調出題"])
    with tabs[0]:
        st.subheader("選擇渠道與版位")
        channels = st.multiselect("選擇渠道", ["FB_動態","IG_限時","Google_搜尋","YouTube_展示","LINE_好友"])
        st.divider()
        st.subheader("文案建議（每個 TA 五則）")
        ta_list = [n for n,_ in st.session_state.get("ta_clusters",[])]
        copy_dict = {}
        if not ta_list:
            st.info("請先在『TA 預測與圈選』鎖定 TA。")
        for ta in ta_list:
            st.markdown(f"**{ta}**")
            arr = copy_suggestions_for_ta(ta, 5)
            copy_dict[ta] = arr
            for i, s in enumerate(arr,1):
                st.write(f"{i}. {s}")
            st.write("---")
        st.subheader("圖片版型 Wireframe 建議")
        st.write("A 情境寫實｜B 產品特寫｜C 前後對比；提供 1:1 / 4:5 / 16:9 尺寸與標題/副標/CTA/Logo 安全區")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("匯出 CSV（文案）"):
                data, fname = export_copy_csv(copy_dict)
                st.download_button("下載 copy_suggestions.csv", data, file_name="copy_suggestions.csv", mime="text/csv")
        with col2:
            if st.button("匯出 圖片版型規格（TXT）"):
                txt = spec_text(channels)
                st.download_button("下載 image_spec.txt", txt, file_name="image_spec.txt")
    with tabs[1]:
        st.subheader("市調出題")
        st.write("問卷結構")
        st.json({
            "封閉題": ["Q1: 您的年齡？", "Q2: 您過去3個月是否購買過本類商品？"],
            "開放題": ["Q3: 影響您購買的最重要原因是？"],
            "情境題(虛擬消費者Q&A)": ["Q4: 如果看到『新品搶先』的貼文，您會？"]
        })
        st.write("題目編輯器（示意）")
        st.text_area("編輯題幹/選項/跳題規則", height=120)
        col1, col2, col3, col4 = st.columns(4)
        col1.button("AI 產生題組")
        col2.button("匯入樣板")
        col3.button("預覽")
        if col4.button("發送"):
            st.session_state["survey_sent"] = True
            st.session_state["current_module"] = "Module 4｜成效與顧客洞察"
            st.success("已發送問卷，前往成效頁")
            st.rerun()

def module4():
    page_header("成效與顧客洞察")
    tabs = st.tabs(["功能頁面4-1 媒體投放成效與洞察","功能頁面4-2 市調回收成效"])
    with tabs[0]:
        st.subheader("KPI 摘要")
        kpi = kpi_sample()
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
        col1, col2 = st.columns(2)
        if col1.button("加入再行銷提案"):
            st.session_state["is_remarketing"] = True
            st.session_state["current_module"] = "Module 1｜提案目標與報價"
            st.rerun()
        if col2.button("下載週報 CSV"):
            buff = io.BytesIO()
            df.to_csv(buff, index=False)
            st.download_button("下載 performance.csv", data=buff.getvalue(), file_name="performance.csv", mime="text/csv")
    with tabs[1]:
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
        st.download_button("下載 open_coding.csv", data=codes.to_csv(index=False).encode("utf-8-sig"), file_name="open_coding.csv")
        st.write("AI 態度標籤雲：正面 63%｜中立 28%｜負面 9%")

def module5():
    page_header("會員忠誠與再行銷（NES）")
    tabs = st.tabs(["5-1 NES 總覽","5-2 新客預測與放大","5-3 沉睡客預測與喚醒","5-4 既有客鞏固計畫"])
    with tabs[0]:
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("新客（近30天）", "3,420", "+12%")
        with c2: st.metric("沉睡客（近90天）", "1,180", "-6%")
        with c3: st.metric("活躍會員", "26,540", "+3%")
    with tabs[1]:
        st.write("候選名單（示意）")
        df = pd.DataFrame({"顧客ID":[f"C{i:05d}" for i in range(1,11)],"相似度":[round(random.uniform(0.7,0.95),2) for _ in range(10)]})
        st.dataframe(df)
        if st.button("生成新提案（新客放大）"):
            st.session_state["current_module"] = "Module 1｜提案目標與報價"
            st.rerun()
    with tabs[2]:
        st.write("沉睡風險名單（示意）")
        df = pd.DataFrame({"顧客ID":[f"Z{i:05d}" for i in range(1,11)],"流失機率":[round(random.uniform(0.6,0.9),2) for _ in range(10)]})
        st.dataframe(df)
        if st.button("生成新提案（喚醒計畫）"):
            st.session_state["current_module"] = "Module 1｜提案目標與報價"
            st.rerun()
    with tabs[3]:
        st.write("忠誠活動建議（示意）")
        st.markdown("- 會員日：每月第 1 週末雙倍點數\n- 新品試用組合包\n- 高價值客戶 VIP 線下體驗")
        st.write("採納追蹤")
        st.checkbox("已採納：會員日雙倍點數")
        st.checkbox("已採納：新品試用組合包")

def module6():
    page_header("產業報告（Insight Center）")
    tabs = st.tabs(["6-1 重點客戶／主力客群","6-2 提案分析／會員健檢","6-3 OpenData 報告"])
    with tabs[0]:
        st.write("主力客群與趨勢（示意）")
        st.dataframe(pd.DataFrame({
            "客群":["年輕都會女性","有毛孩家庭","健身重訓者"],
            "近季消費力變化(%)":[+8,-3,+5]
        }))
        st.download_button("下載 PPT（示意）", data=b"Placeholder PPT bytes", file_name="insight_placeholder.pptx")
    with tabs[1]:
        st.write("會員健檢（五面向燈號）")
        df = pd.DataFrame({"面向":["情感","功能","價格","會員","體驗"],"燈號":["🟢","🟡","🟢","🟡","🟢"]})
        st.dataframe(df)
        with st.expander("訂閱定期發送"):
            freq = st.selectbox("頻率", ["每月","每季"])
            email = st.text_input("寄送對象 Email")
            st.button("建立訂閱")
    with tabs[2]:
        st.write("OpenData 區域/產業底稿（示意）")
        st.dataframe(pd.DataFrame({
            "指標":["人口數","批發零售營業額","餐飲營業額","CPI"],
            "值":["2,450,000","+3.1%","+4.2%","+2.3%"]
        }))

# ---------- Main ----------

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")
    init_state()
    if not st.session_state["authed"]:
        page_login()
        return

    # Draw global sidebar before routing so nav changes apply immediately
    global_sidebar()

    module = st.session_state.get("current_module", NAV_OPTIONS[0])
    if module.startswith("Module 1"):
        module1()
    elif module.startswith("Module 2"):
        module2()
    elif module.startswith("Module 3"):
        module3()
    elif module.startswith("Module 4"):
        module4()
    elif module.startswith("Module 5"):
        module5()
    elif module.startswith("Module 6"):
        module6()
    else:
        module1()

if __name__ == "__main__":
    main()
