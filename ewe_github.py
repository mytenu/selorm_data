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
CLIENT = init_connection()
client1=clients.open("ewe_dataset_users").sheet1
client2 = clients.open("ewe_dataset").sheet1

# Initialize session state for login status
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

st.title("Ewe Dataset Hub")

# Check if user is logged in
if st.session_state.logged_in:
    # Admin Dashboard
    if st.session_state.is_admin:
        st.header("Admin Dashboard")
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.is_admin = False 
            st.rerun()
        
        # Get data and display (moved outside the logout button logic)
        users = client1.get_all_records()
        dataset = client2.get_all_records()
        
        st.header("Ewe-English Dataset")
        df = pd.DataFrame(dataset)
        st.dataframe(df)
        
        st.header("All users")
        dff = pd.DataFrame(users)
        st.dataframe(dff)
        
    # Regular User Data Collection Page    
    else:
        st.header(f"Welcome, {st.session_state.username}!")
        
        # Logout button
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.is_admin = False
            st.rerun()
        
        # Data Collection Form
        st.subheader("Data Collection Form")
        
        with st.form("data_collection"):
            selected_date = st.date_input("Select date", value=date.today())
            
            # Add your data collection fields here
            ewe = st.text_input("Enter Ewe Sentence")
            english = st.text_area("Enter English Translation")
            
            if st.form_submit_button("Submit Data"):
                # Save data to Google Sheets
                client2.append_row([
                    selected_date.strftime("%Y-%m-%d"),
                    ewe,
                    english,
                    st.session_state.username,
                ])
                st.success("Data submitted successfully!")

else:
    # Login/Registration Page
    tab1, tab2= st.tabs(["Login", "Register"])
    
    with tab2:
        with st.form("Registration"):
            users= client1.get_all_records()
            name = st.text_input("Enter Name").strip()
            username= st.text_input("Enter Username/Nickname").strip()
            password = st.text_input("Enter Password", type= "password").strip() 
            repassword = st.text_input("Repeat Password", type="password").strip()
            if st.form_submit_button("Register"):
                if password != repassword:
                    st.error("your passwords do not match")
                else:
                    client1.append_row([username, password, name])
                    st.success("Registration Successful")
    
    with tab1:
        with st.form("Login"):
            users= client1.get_all_records()
            dataset=client2.get_all_records()
            username100 = st.text_input("Enter Username/Nickname").strip().lower()
            password100= st.text_input("Enter Password", type= "password").strip()
            if st.form_submit_button("Login"):
                found = False
                if username100 == "admin" and password100 == "1345":
                    st.session_state.logged_in = True
                    st.session_state.username = "admin"
                    st.session_state.is_admin = True  # This was missing!
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
                        st.error("wrong login details")