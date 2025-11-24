import streamlit as st
from model_logic import analyze_interactions, load_search_history # Import the new function

# Page Config
st.set_page_config(page_title="MedSafe AI", page_icon="💊")

# Sidebar
st.sidebar.title("MedSafe AI 🛡️")
st.sidebar.info("This tool uses Google's Gemini AI to check for potential interactions between your meds, diet, and conditions.")
st.sidebar.markdown("---")
st.sidebar.caption("Built for BNB Marathon 2025")

# User Identification (Critical for history)
st.markdown("### 👤 User Profile")
user_id = st.text_input("Enter a unique User ID (e.g., 'JohnSmith') to save your history.", key="user_id_input")

# History Section
if user_id:
    if st.button("Load Past Searches (History)"):
        history = load_search_history(user_id)
        if history:
            st.markdown("#### Your Last 5 Searches:")
            st.dataframe(history)
        else:
            st.info(f"No previous searches found for user '{user_id}'.")


# Main UI
st.title("💊 Medication Interaction Checker")
st.markdown("Enter your details below to check for safety alerts.")

with st.form("medical_form"):
    
    st.markdown("---")
    st.markdown("#### Required Information")
    meds = st.text_area("Medications (comma separated)", placeholder="e.g., Warfarin, Aspirin", height=70)
    condition = st.text_input("Medical Conditions", placeholder="e.g., High Blood Pressure")
    
    st.markdown("---")
    st.markdown("#### Lifestyle & Diet")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        diet = st.text_input("Dietary Habits / Specific Foods", placeholder="e.g., Grapefruit, Spinach")
    with col2:
        alcohol = st.text_input("Alcohol Intake (weekly)", placeholder="e.g., Occasional glass of wine")
    with col3:
        smoking = st.selectbox("Smoking Status", ["Non-smoker", "Occasional", "Daily"])

    submitted = st.form_submit_button("Analyze Safety 🔍", type="primary", disabled=(not user_id))

    if not user_id:
        st.warning("Please enter a User ID above to enable the analysis.")

if submitted:
    if not meds:
        st.warning("Please enter at least one medication.")
    else:
        with st.spinner("Consulting Gemini AI..."):
            # CRITICAL: Pass the user_id and new lifestyle factors
            response = analyze_interactions(user_id, meds, condition, diet, alcohol, smoking) 
            st.markdown("### Analysis Result")
            st.markdown(response)
            st.success("Analysis complete. Results saved to your history.")