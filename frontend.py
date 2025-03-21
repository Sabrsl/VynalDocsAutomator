import streamlit as st
import requests

st.set_page_config(page_title="Vynal Docs Automator Web", layout="wide")

st.title("Vynal Docs Automator - Version Web")

uploaded_file = st.file_uploader("Chargez un fichier", type=["csv", "docx", "pdf"])

if uploaded_file is not None:
    files = {"file": uploaded_file.getvalue()}
    response = requests.post("http://127.0.0.1:8000/upload/", files=files)
    st.success(response.json()["message"])
