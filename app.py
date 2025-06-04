import streamlit as st
import pandas as pd
import json
import os
from dotenv import load_dotenv
import streamlit_authenticator as stauth

load_dotenv()

# ========================
# 🔐 認証処理
# ========================
def perform_authentication():
    credentials = json.loads(os.environ["CREDENTIALS"])
    cookie = json.loads(os.environ["COOKIE"])

    authenticator = stauth.Authenticate(
        credentials,
        cookie['name'],
        cookie['key'],
        cookie['expiry_days'],
    )

    authenticator.login("ログイン", "main")

    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None
    if st.session_state["authentication_status"] is False:
        st.error("ユーザー名かパスワードが間違っています")
        st.stop()
    elif st.session_state["authentication_status"] is None:
        st.warning("ログインしてください")
        st.stop()

    return authenticator


# ========================
# 📦 データ読み込み
# ========================
def safe_read_csv(path, name):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.warning(f"{name} ファイルが見つかりません: {path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"{name} の読み込みに失敗しました: {e}")
        return pd.DataFrame()

base_path = "data"
df_employees = safe_read_csv(os.path.join(base_path, "employee_data.csv"), "社員情報").sort_values(by="employeeCode", na_position="last")
df_divisions = safe_read_csv(os.path.join(base_path, "division_staffs.csv"), "部署情報")
df_properties = safe_read_csv(os.path.join(base_path, "prop_staffs.csv"), "物件情報")
df_designs = safe_read_csv(os.path.join(base_path, "person_hour_reports.csv"), "設計情報")
df_opportunities = safe_read_csv(os.path.join(base_path, "opportunity_staffs.csv"), "反響情報")
df_sales = safe_read_csv(os.path.join(base_path, "sales_staffs.csv"), "販売情報")
df_seats = safe_read_csv(os.path.join(base_path, "seat_data.csv"), "座席情報")

if df_seats.empty:
    df_seats = pd.DataFrame(columns=['employeeCode', 'seatNumber', 'status'])
else:
    df_seats = df_seats[['employeeCode', 'seatNumber', 'status']].drop_duplicates()
    df_seats['employeeCode'] = df_seats['employeeCode'].astype(str)

# ========================
# 🖼️ プロフィール画像
# ========================
def load_profile_image_map():
    try:
        with open(os.path.join(base_path, "profile_image.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["employeeCode"]: item["photo_path"].strip() for item in data}
    except Exception as e:
        st.error(f"プロフィール画像読み込み失敗: {e}")
        return {}

image_map = load_profile_image_map()

# ========================
# 🧠 ロジック関数
# ========================
def fetch_employee_info(email):
    filtered = df_divisions[df_divisions['Email'] == email]
    companies = filtered['Company'].dropna().astype(str).unique().tolist()
    divisions = filtered['Division'].dropna().astype(str).unique().tolist()
    return "\n".join(companies) or "情報なし", "\n".join(divisions) or "情報なし"

def fetch_employee_projects(code, email):
    projects = []

    for _, row in df_properties[df_properties['StaffCode_Prop'] == code].iterrows():
        projects.append(f"{row['ProjectName']} 物件")

    for _, row in df_designs[df_designs['email_Design'] == email].iterrows():
        pj_row = df_properties[df_properties['PJCD'] == row['PJCD']]
        if not pj_row.empty:
            projects.append(f"{pj_row.iloc[0]['ProjectName']} 設計")

    opp_pj = set(df_properties[df_properties['PJCD'].isin(df_opportunities[df_opportunities['EMAIL_OPPORTUNITY'] == email]['PJCD'])]['ProjectName'])
    sales_pj = set(df_properties[df_properties['PJCD'].isin(df_sales[df_sales['employeeCode'] == code]['PJCD'])]['ProjectName'])

    for pj in opp_pj & sales_pj:
        projects.append(f"{pj} 反響・販売")
    for pj in opp_pj - sales_pj:
        projects.append(f"{pj} 反響")
    for pj in sales_pj - opp_pj:
        projects.append(f"{pj} 販売")

    return "\n".join(projects) if projects else None

def fetch_same_division_members(email, code):
    divisions = df_divisions[df_divisions['Email'] == email]['Division'].dropna().unique()
    result = {}
    for div in divisions:
        members = []
        same_div = df_divisions[df_divisions['Division'] == div].drop_duplicates(subset='Email')
        for _, member in same_div.iterrows():
            if member['Email'] == email:
                continue
            info = df_employees[df_employees['Email'] == member['Email']]
            if not info.empty:
                members.append({
                    'name': info.iloc[0]['displayName'],
                    'email': member['Email'],
                    'employeeCode': info.iloc[0]['employeeCode']
                })
        if members:
            result[div] = members
    return result

def fetch_avatar_url(code):
    path = image_map.get(code)
    return os.path.normpath(path) if path else f"https://api.dicebear.com/9.x/avataaars/svg?seed={code}"

# ========================
# 🖼️ 表示用関数
# ========================
def display_profile_sidebar(name, email, code, seat, status, company, division, projects, members):
    with st.sidebar:
        st.subheader(f"{name}のプロフィール詳細")
        st.image(fetch_avatar_url(code), width=150)
        st.write(f"📧 {email}")
        st.write(f"🆔 {code}")
        st.write(f"🪑 {seat or '-'}")
        st.write(f"⚙️ {status or '-'}")
        st.write(f"🏢 {company}")
        st.write(f"📦 {division}")
        if projects:
            st.write("📌 **担当プロジェクト:**")
            for p in projects.split("\n"):
                st.write(f"- {p}")
        if members:
            for div, group in members.items():
                st.write(f"👥 **{div} のメンバー:**")
                for m in group:
                    if st.button(m['name'], key=f"member_{m['employeeCode']}"):
                        st.session_state.selected_member = m['email']
                        st.rerun()

def display_employee_details(row):
    company, division = fetch_employee_info(row["Email"])
    projects = fetch_employee_projects(row["employeeCode"], row["Email"])
    members = fetch_same_division_members(row["Email"], row["employeeCode"])
    display_profile_sidebar(row['displayName'], row['Email'], row['employeeCode'], row['seatNumber'], row['status'], company, division, projects, members)

# ========================
# 🚀 アプリ実行
# ========================
authenticator = perform_authentication()

if st.button("ログアウト", key="logout_main"):
    st.session_state.clear()
    authenticator.logout("ログアウト", "main")
    st.rerun()

st.title("社員一覧")

query_name = st.text_input("名前で検索")
query_company = st.selectbox("会社で検索", ["すべて"] + df_divisions['Company'].dropna().unique().tolist())
query_division = st.selectbox("部署で検索", ["すべて"] + sorted(df_divisions['Division'].dropna().unique().tolist()))

filtered_employees = df_employees.copy()
if query_name:
    filtered_employees = filtered_employees[filtered_employees['displayName'].str.contains(query_name, case=False, na=False)]
if query_company != "すべて":
    filtered_employees = filtered_employees[filtered_employees['Email'].isin(df_divisions[df_divisions['Company'] == query_company]['Email'])]
if query_division != "すべて":
    filtered_employees = filtered_employees[filtered_employees['Email'].isin(df_divisions[df_divisions['Division'] == query_division]['Email'])]

filtered_employees = filtered_employees.drop_duplicates(subset='Email')

for idx, row in filtered_employees.iterrows():
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    col1.write(row["employeeCode"])
    col2.write(row["displayName"])
    col3.write(f"{row['seatNumber'] or ''} {row['status'] or ''}")
    if col4.button("詳細", key=f"{row['employeeCode']}_{idx}"):
        display_employee_details(row)

if 'selected_member' in st.session_state:
    selected_member = st.session_state['selected_member']
    selected = df_employees[df_employees['Email'] == selected_member].iloc[0]
    display_employee_details(selected)
