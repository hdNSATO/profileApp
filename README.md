# 社員情報可視化アプリ

このアプリケーションは Streamlit を使用して、社員情報を検索・表示・閲覧できる社内向けツールです。ログイン後に名前・会社・部署・プロジェクトなどで社員を検索し、詳細プロフィールを表示できます。

## 🔧 セットアップ手順

### 1. 必要ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. secrets.toml の作成（`.streamlit/secrets.toml`）

```toml
[credentials]
  [credentials.usernames.sample_user]
  name = "sample_user"
  email = "sample@email.com"
  password = "$2b$12$NsNIvSxA9ofB7FvtC1X0YOTYFpQcl2JkSjqp2d.04PCvMm2QdvuFq"

[cookie]
expiry_days = 1
key = "some_signature_key"
name = "some_cookie_name"
```

> パスワードのハッシュ化には、`create_yaml.py` スクリプトで対応できます（必須ではありません）。

### 3. アプリの実行

```bash
streamlit run streamlit_app.py
```

## 🔐 認証について

このアプリでは [`streamlit-authenticator`](https://github.com/mkhorasani/Streamlit-Authenticator) を使用してログイン認証を行います。ユーザー情報は `secrets.toml` に保存され、パスワードは bcrypt で安全にハッシュ化されます。

## 📁 データ構成（data フォルダ）

- `employee_data.csv`: 社員基本情報
- `division_staffs.csv`: 所属部署情報
- `prop_staffs.csv`: 物件プロジェクト情報
- `person_hour_reports.csv`: 設計プロジェクト情報
- `opportunity_staffs.csv`: 反響担当者情報
- `sales_staffs.csv`: 販売担当者情報
- `seat_data.csv`: 座席配置情報
- `profile_image.json`: プロフィール画像パス

## 💡 機能一覧

- 社員の名前・会社・部署・プロジェクトで検索
- プロフィール詳細表示（座席、所属、プロジェクト、部署メンバー）
- 部署ごとのメンバー表示
- セッションに基づくログイン管理・ログアウト

## 📦 必須ライブラリ

- streamlit
- pandas
- streamlit-authenticator
- pyyaml
- python-dotenv

## 📝 ライセンス

MIT License
