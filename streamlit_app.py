import streamlit as st
import pandas as pd
import json
import os
import msal
import requests
from dotenv import load_dotenv
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

load_dotenv()

# ========================
# 🔐 認証関連（Streamlit Authenticator）
# ========================
# 認証用設定ファイルの読み込み
config = st.secrets

# 認証用のハッシュ関数を作成
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# ログインフォームの表示（最初に必ず呼び出す）
authenticator.login('ログイン', 'main')

# ログイン状態の確認
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
if st.session_state["authentication_status"] is False:
    st.error("ユーザー名かパスワードが間違っています")
    st.stop()
elif st.session_state["authentication_status"] is None:
    st.warning("ログインしてください")
    st.stop()

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
df_employee = safe_read_csv(os.path.join(base_path, "employee_data.csv"), "社員情報").sort_values(by="employeeCode", na_position="last")
df_division = safe_read_csv(os.path.join(base_path, "division_staffs.csv"), "部署情報")
df_prop = safe_read_csv(os.path.join(base_path, "prop_staffs.csv"), "物件情報")
df_design = safe_read_csv(os.path.join(base_path, "person_hour_reports.csv"), "設計情報")
df_opportunity = safe_read_csv(os.path.join(base_path, "opportunity_staffs.csv"), "反響情報")
df_sales = safe_read_csv(os.path.join(base_path, "sales_staffs.csv"), "販売情報")
df_seat = safe_read_csv(os.path.join(base_path, "seat_data.csv"), "座席情報")

# 仮の座席データ
if df_seat.empty:
    df_seat = pd.DataFrame({
        'employeeCode': [],
        'seatNumber': [],
        'status': []
    })
else:
    df_seat = df_seat[['employeeCode', 'seatNumber', 'status']].drop_duplicates()
    df_seat['employeeCode'] = df_seat['employeeCode'].astype(str)
    

# プロフィール画像読み込み
def load_image_map():
    try:
        with open(os.path.join(base_path, "profile_image.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["employeeCode"]: item["photo_path"].strip() for item in data}
    except Exception as e:
        st.error(f"プロフィール画像読み込み失敗: {e}")
        return {}

image_map = load_image_map()

# ========================
# 🧠 ロジックヘルパー
# ========================
def get_employee_info(email):
    filtered = df_division[df_division['Email'] == email]
    companies = filtered['Company'].dropna().astype(str).unique().tolist()
    divisions = filtered['Division'].dropna().astype(str).unique().tolist()
    return "\n".join(companies) if companies else "情報なし", "\n".join(divisions) if divisions else "情報なし"

def get_employee_projects(code, email):
    pjs = []
    for _, row in df_prop[df_prop['StaffCode_Prop'] == code].iterrows():
        pjs.append(f"{row['ProjectName']} 物件")
    for _, row in df_design[df_design['email_Design'] == email].iterrows():
        pj_row = df_prop[df_prop['PJCD'] == row['PJCD']]
        if not pj_row.empty:
            pjs.append(f"{pj_row.iloc[0]['ProjectName']} 設計")
    opportunity = set(df_prop[df_prop['PJCD'].isin(df_opportunity[df_opportunity['EMAIL_OPPORTUNITY'] == email]['PJCD'])]['ProjectName'])
    sales = set(df_prop[df_prop['PJCD'].isin(df_sales[df_sales['employeeCode'] == code]['PJCD'])]['ProjectName'])
    for pj in opportunity & sales:
        pjs.append(f"{pj} 反響・販売")
    for pj in opportunity - sales:
        pjs.append(f"{pj} 反響")
    for pj in sales - opportunity:
        pjs.append(f"{pj} 販売")
    return "\n".join(pjs) if pjs else None

def get_same_division_members(email, code):
    divisions = df_division[df_division['Email'] == email]['Division'].dropna().unique()
    result = {}
    for div in divisions:
        members = []
        same = df_division[df_division['Division'] == div].drop_duplicates(subset='Email')
        for _, m in same.iterrows():
            if m['Email'] == email:
                continue
            info = df_employee[df_employee['Email'] == m['Email']]
            if not info.empty:
                members.append({
                    'name': info.iloc[0]['displayName'],
                    'email': m['Email'],
                    'employeeCode': info.iloc[0]['employeeCode']
                })
        if members:
            result[div] = members
    return result

def get_avatar(code):
    path = image_map.get(code)
    return os.path.normpath(path) if path else f"https://api.dicebear.com/9.x/avataaars/svg?seed={code}"

# ========================
# 🖼️ UI表示
# ========================
def profile_card(name, email, code, seat, status, company, division, projects, members):
    with st.sidebar:
        st.subheader(f"{name}のプロフィール詳細")
        st.image(get_avatar(code), width=150)
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
                        st.rerun()  # rerun

def display_employee_details(row):
    company, division = get_employee_info(row["Email"])
    projects = get_employee_projects(row["employeeCode"], row["Email"])
    members = get_same_division_members(row["Email"], row["employeeCode"])
    profile_card(row['displayName'], row['Email'], row['employeeCode'], row['seatNumber'], row['status'], company, division, projects, members)

# ========================
# 🚀 アプリメイン
# ========================
if "authentication_status" in st.session_state and st.session_state["authentication_status"]:
    if st.button("ログアウト", key="logout_main"):
        # セッション状態をクリア
        st.session_state.clear()  # セッション情報をクリア
        
        # クッキーの削除（必要に応じて）
        authenticator.logout("ログアウト", "main")
        
        # ログアウト後、画面を再実行（リロード）
        st.rerun()  # ここで画面をリロード
        
    st.title("社員一覧")

    search_name = st.text_input("名前で検索")
    search_company = st.selectbox("会社で検索", ["すべて"] + df_division['Company'].dropna().unique().tolist())
    search_division = st.selectbox("部署で検索", ["すべて"] + sorted(df_division['Division'].dropna().unique().tolist()))
    search_project = st.selectbox("プロジェクトで検索", ["すべて"] + df_prop['ProjectName'].dropna().unique().tolist())

    filtered = df_employee.copy()
    if search_name:
        filtered = filtered[filtered['displayName'].str.contains(search_name, case=False, na=False)]
    if search_company != "すべて":
        filtered = filtered[filtered['Email'].isin(df_division[df_division['Company'] == search_company]['Email'])]
    if search_division != "すべて":
        filtered = filtered[filtered['Email'].isin(df_division[df_division['Division'] == search_division]['Email'])]

    filtered = filtered.drop_duplicates(subset='Email')

    for idx, row in filtered.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        col1.write(row["employeeCode"])
        col2.write(row["displayName"])
        col3.write(f"{row['seatNumber'] or ''} {row['status'] or ''}")
        if col4.button("詳細", key=f"{row['employeeCode']}_{idx}"):
            display_employee_details(row)

    if 'selected_member' in st.session_state:
        selected_member = st.session_state['selected_member']
        selected = df_employee[df_employee['Email'] == selected_member].iloc[0]
        display_employee_details(selected)
else:
    st.warning("ログインしてください")
