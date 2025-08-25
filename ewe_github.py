import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date

# Define scope
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials from Streamlit secrets
@st.cache_resource
def init_connection():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(credentials)
    return client

# Initialize connection
clients = init_connection()
client1=clients.open("ewe_dataset_users").sheet1
client2 = clients.open("ewe_dataset").sheet1

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

st.title("Ewe Dataset Hub")

# ---------------- ADMIN DASHBOARD ----------------
if st.session_state.is_admin:
    st.header("Admin Dashboard")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.rerun()

    # Load data
    users = client1.get_all_records()
    dataset = client2.get_all_records()

    st.header("Ewe-English Dataset")
    df = pd.DataFrame(dataset)
    st.dataframe(df)

    st.header("All Users")
    dff = pd.DataFrame(users)
    st.dataframe(dff)

    # 🔹 Contribution statistics
    if not df.empty and "username" in df.columns:
        st.subheader("User Contribution Statistics")
        username_counts = df["username"].value_counts().reset_index()
        username_counts.columns = ["Username", "Entries Count"]

        st.dataframe(username_counts)
        st.bar_chart(username_counts.set_index("Username"))

    # 🔹 Delete a user from USERS sheet
    st.subheader("Manage Users")
    if not dff.empty and "username" in dff.columns:
        user_to_delete = st.selectbox("Select user to delete", options=dff["username"].tolist())
        if st.button("Delete User"):
            users_list = client1.get_all_records()
            for i, user in enumerate(users_list, start=2):  # row 2 = first user
                if user["username"] == user_to_delete:
                    client1.delete_rows(i)
                    st.success(f"User '{user_to_delete}' deleted successfully!")
                    st.rerun()

    # 🔹 Delete all contributions by a username
    st.subheader("Manage Contributions")
    if not df.empty and "username" in df.columns:
        contrib_user = st.selectbox("Select user to delete contributions", options=df["username"].unique().tolist())
        if st.button("Delete All Contributions"):
            dataset_rows = client2.get_all_records()
            rows_to_delete = [i for i, row in enumerate(dataset_rows, start=2) if row["username"] == contrib_user]

            for row_index in reversed(rows_to_delete):  # delete bottom-to-top
                client2.delete_rows(row_index)

            st.success(f"All contributions by '{contrib_user}' deleted successfully!")
            st.rerun()

# ---------------- USER DASHBOARD ----------------
elif st.session_state.logged_in:
    st.header(f"Welcome, {st.session_state.username}!")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.rerun()

    # Data Collection Form
    st.subheader("Data Collection Form")
    with st.form("data_collection"):
        selected_date = st.date_input("Select date", value=date.today())
        ewe = st.text_input("Enter Ewe Sentence")
        english = st.text_area("Enter English Translation")

        if st.form_submit_button("Submit Data"):
            client2.append_row([
                selected_date.strftime("%Y-%m-%d"),
                ewe,
                english,
                st.session_state.username,
            ])
            st.success("Data submitted successfully!")

    # 🔹 Show user's monthly contributions
    dataset = client2.get_all_records()
    df = pd.DataFrame(dataset)
    if not df.empty and "username" in df.columns and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        user_df = df[df["username"] == st.session_state.username]

        if not user_df.empty:
            user_df["month"] = user_df["date"].dt.to_period("M")
            monthly_counts = user_df.groupby("month").size().reset_index(name="Entries")

            st.subheader("Your Monthly Contributions")
            st.dataframe(monthly_counts)
            st.line_chart(monthly_counts.set_index("month"))
        else:
            st.info("You have not contributed any entries yet.")

# ---------------- LOGIN / REGISTER ----------------
else:
    tab1, tab2 = st.tabs(["Login", "Register"])

    # Registration
    with tab2:
        with st.form("Registration"):
            users = client1.get_all_records()
            name = st.text_input("Enter Name").strip()
            username = st.text_input("Enter Username/Nickname").strip()
            password = st.text_input("Enter Password", type="password").strip()
            repassword = st.text_input("Repeat Password", type="password").strip()

            if st.form_submit_button("Register"):
                if password != repassword:
                    st.error("Your passwords do not match")
                else:
                    client1.append_row([username, password, name])
                    st.success("Registration Successful")

    # Login
    with tab1:
        with st.form("Login"):
            users = client1.get_all_records()
            dataset = client2.get_all_records()
            username100 = st.text_input("Enter Username/Nickname").strip().lower()
            password100 = st.text_input("Enter Password", type="password").strip()

            if st.form_submit_button("Login"):
                found = False
                if username100 == "admin" and password100 == "1345":
                    st.session_state.logged_in = True
                    st.session_state.username = "admin"
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    for user in users:
                        if str(user["username"]).lower() == username100 and str(user["password"]) == password100:
                            found = True
                            st.session_state.logged_in = True
                            st.session_state.username = username100
                            st.session_state.is_admin = False
                            st.rerun()
                            break
                    if not found:
                        st.error("Wrong login details")
