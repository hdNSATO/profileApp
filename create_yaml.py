import streamlit_authenticator as stauth

# 'passwords' 引数を渡す
passwords = ['sample']
hasher = stauth.Hasher(passwords)
hashed_passwords = hasher.generate()

print(hashed_passwords)
