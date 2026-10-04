import re
import pandas as pd
import streamlit as st

# =============================================================================
# 1. SECURITY & DATA SANITIZATION UTILITIES
# =============================================================================

def clean_text(text: str) -> str:
    """Removes problematic characters like tabs, newlines, and trailing spaces

    that break CSV/Google Sheets parsers.
    """
    if not text:
        return ""
    # Strip leading/trailing whitespaces
    text = text.strip()
    # Replace newlines and tabs with standard single spaces
    text = re.sub(r"[\r\n\t]+", " ", text)
    # Remove hidden control characters or illegal Excel/GSheet punctuation symbols if needed
    text = re.sub(r'[^\x20-\x7E]', '', text) 
    return text


# =============================================================================
# 2. LOGIN GATEWAY
# =============================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")

    user_id = st.text_input("Username / User ID")
    user_password = st.text_input("Password", type="password")

    if st.button("Login"):
        if (
            user_id == "PictureDivinity"
            and "imagineinfinity" == user_password
        ):
            st.session_state.logged_in = True
            st.session_state.user_id = user_id
            st.rerun()
        else:
            st.error("Invalid User ID or Password. Access Denied.")
    st.stop()  # Halt execution until logged in

# =============================================================================
# 3. CORE DATA LOADING
# =============================================================================
# Direct live CSV conversion link from your public-but-obscured Google Sheet
GSHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/1EUc_dEcjPBhRRV4YFRa6QF6VyjgXNG3mj7b_9GS2f10/export?format=csv"
)


@st.cache_data(ttl=10)  # Caches for 10 seconds to save bandwidth but keeps data fresh
def load_data():
    try:
        return pd.read_csv(GSHEET_CSV_URL)
    except Exception as e:
        st.error(f"Error connecting to data source: {e}")
        return pd.DataFrame()  # Fallback empty dataframe


df = load_data()

if df.empty:
    st.warning("The exercise database is empty or inaccessible.")
    st.stop()

# =============================================================================
# 4. APP NAVIGATION FLOW
# =============================================================================
st.sidebar.title(f"Welcome, {st.session_state.user_id} 👋")
app_mode = st.sidebar.radio(
    "Choose Action:", ["⚡ Run Random Exercise Selector", "➕ Append New Exercise Data"]
)

# =============================================================================
# MODE A: MAIN LOGIC / ANALYTICS
# =============================================================================
if app_mode == "⚡ Run Random Exercise Selector":
    st.title("🏋️‍♂️ Random Exercise Selector")

    unique_options = sorted(df['target'].unique().tolist())


    # Dropdown input from user
    user_selection = st.selectbox(
        "Select Target :", unique_options
    )

    st.markdown("---")

    # --- YOUR MAIN LOGIC ---
    def run_main_logic(df, tar):
        """YOUR ORIGINAL LOGIC HERE.
        Takes a DataFrame, operates on the selection, and outputs a clean result
        DataFrame.
        """
        # Placeholder example: filter rows matching selection
        a=df[df['target']==tar]

        up=a[a['warmup-down']=='up']
        dwn=a[a['warmup-down']=='down']
        nul=a[a['warmup-down'].isna()]
        time=0
        p1=pd.DataFrame()
        p2=pd.DataFrame()
        p3=pd.DataFrame()
        while time<50 and time<40:                     #///////////////change acc to proper time data
            r1=up.sample()
            r2=nul.sample()
            r3=dwn.sample()
            p1=pd.concat([p1,r1])
            p2=pd.concat([p2,r2])
            p3=pd.concat([p3,r3])
            up=up.drop(r1.index)
            nul=nul.drop(r2.index)
            dwn=dwn.drop(r3.index)
            time=sum(p1['time'])+sum(p2['time'])+sum(p3['time'])
        #     print(time)
        
        result=pd.concat([p1,p2,p3])
        result.index=range(1,len(result)+1)
        return (result, time)

    # Run execution and display results
    if st.button("Execute Process"):
        with st.spinner("Processing data..."):
            result_df, time = run_main_logic(df, user_selection)

            st.subheader("📊 Output Results")
            if not result_df.empty:
                st.dataframe(result_df, use_container_width=True)
                st.write("expected time:",time)
            else:
                st.info("No matching records derived from current operations.")


# =============================================================================
# MODE B: APPEND NEW DATA WITH VALIDATION CHECKS
# =============================================================================
elif app_mode == "➕ Append New Exercise Data":
    st.title("📝 Data Entry Registry")
    st.write("Fill out the validated form below to register new rows.")

    with st.form("exercise_append_form", clear_on_submit=True):
        # 1. Dropdown Menu Input
        target = st.selectbox(
            "Target Muscle:",
            ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"],
        )
        
        name = st.text_input("Exercise Name (Text Entry):")
        
        intensity = st.selectbox(
            "intensity:",
            ["high", "low", "med"],
        )
        
        warmup = st.selectbox(
            "Warmup cooldown or neither:",
            ["Neither", "Cooldown","Warmup"],
        )
        if warmup =="Warmup":
            warmup="up"
        elif warmup== "Cooldown":
            warmup="down"
        else:
            warmup="null"
        
        # 2. Integer Input with Range Constraints (e.g., between 1 and 10 sets)
        time = st.number_input(
            "Time:",
            min_value=15,
            max_value=100,
            value=45,
            step=5,
        )

        # 3. String Input with Character Checks
#         form_notes = st.text_area("Form Technique / Instructions:")

        submit_data = st.form_submit_button("Submit & Sync Row")

    if submit_data:
        # Pre-execution structural checks
        clean_title = clean_text(name)
        
        # Validation Guardrails
        if not clean_title:
            st.error("Submission failed: 'Exercise Name' empty or invalid.")

        elif len(clean_title) < 3:
            st.error(
                "Submission failed: Name is too short (Minimum 3 characters)."
            )

        else:
            # Construct the new row matching your structural columns
            new_row = {
                "name": name,
                "time": int(time),
                "intensity":intensity,
                "target": target,
                "warmup-down": warmup,
            }

            # --- HOW DATA IS APPENDED ---
            # Standard dataframe appending locally for display simulation
            new_df_row = pd.DataFrame([new_row])
            simulated_updated_df = pd.concat([df, new_df_row], ignore_index=True)

            # NOTE: Because it is an unauthenticated Google Sheet link, pd.to_csv(GSHEET_CSV_URL)
            # will return an HTTP Error. To append this live, you will want to replace the rows below
            # with your exact Google Sheet updating script block!
            st.success("Data successfully verified, scrubbed, and processed!")
            st.subheader("Preview of Appended Line Item:")
            st.json(new_row)
