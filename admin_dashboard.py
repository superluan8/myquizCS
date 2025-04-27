import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# --- CONFIG ---
ADMIN_PASSWORD = "rhino123"

# --- DATABASE CONNECTION ---
engine = create_engine('sqlite:///quiz_results.db')

# --- FUNCTIONS ---
@st.cache_data
def load_results():
    df = pd.read_sql('SELECT * FROM adaptive_results', con=engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# --- STREAMLIT APP ---

# --- LOGIN SCREEN ---
st.title("🔒 Admin Dashboard Login")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password_attempt = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password_attempt == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Incorrect password.")
    st.stop()

# --- MAIN DASHBOARD ---
st.title("📊 Admin Dashboard - Adaptive Math Quiz Results")

# --- LOAD DATA ---
df = load_results()

# --- SIDEBAR BACKUP (no more danger zone) ---
if not df.empty:
    st.sidebar.download_button(
        label="📥 Download All Results (Backup)",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="quiz_results_backup.csv",
        mime="text/csv"
    )

# --- MAIN CONTENT ---
if df.empty:
    st.warning("⚠️ No quiz results found yet!")
else:
    st.sidebar.header("🔎 Filters")

    grade_filter = st.sidebar.multiselect(
        "Select Grade Level(s):",
        options=df["grade_level"].unique(),
        default=df["grade_level"].unique()
    )

    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range:",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    filtered_df = df[
        (df["grade_level"].isin(grade_filter)) &
        (df["timestamp"].dt.date >= start_date) &
        (df["timestamp"].dt.date <= end_date)
    ]

    sort_option = st.sidebar.selectbox(
        "Sort by:",
        options=["timestamp", "final_rit", "score_correct"],
        index=0
    )

    ascending_order = st.sidebar.checkbox("Sort Ascending?", value=False)
    filtered_df = filtered_df.sort_values(by=sort_option, ascending=ascending_order)

    st.subheader(f"Showing {len(filtered_df)} Results")
    st.dataframe(filtered_df)

    # --- Download Filtered Results
    if not filtered_df.empty:
        st.download_button(
            label="📥 Download Filtered Results",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name="filtered_quiz_results.csv",
            mime="text/csv"
        )

    # --- Quick Summary
    st.subheader("📈 Quick Summary")

    avg_rit = filtered_df["final_rit"].mean()
    avg_score = filtered_df["score_correct"].mean()

    col1, col2 = st.columns(2)
    col1.metric("Average Final RIT Score", f"{avg_rit:.1f}")
    col2.metric("Average Correct Answers", f"{avg_score:.1f} / {filtered_df['score_total'].max()}")

    # --- Bar Chart: Average RIT by Grade
    st.subheader("🎯 Average Final RIT Score by Grade Level")

    if not filtered_df.empty:
        grade_summary = filtered_df.groupby("grade_level")["final_rit"].mean().sort_index()
        fig, ax = plt.subplots()
        ax.bar(grade_summary.index, grade_summary.values)
        ax.set_ylabel("Average Final RIT")
        ax.set_xlabel("Grade Level")
        ax.set_title("Average RIT by Grade")
        st.pyplot(fig)
    else:
        st.info("No data available for selected filters.")

    # --- RIT Growth Trend
    st.subheader("📈 RIT Growth Trend Over Time")

    if not filtered_df.empty:
        time_summary = filtered_df.groupby(filtered_df["timestamp"].dt.to_period("M"))["final_rit"].mean()
        time_summary.index = time_summary.index.to_timestamp()

        fig2, ax2 = plt.subplots()
        ax2.plot(time_summary.index, time_summary.values, marker='o')
        ax2.set_ylabel("Average Final RIT")
        ax2.set_xlabel("Date (Month)")
        ax2.set_title("Average RIT Score Over Time")
        ax2.grid(True)
        st.pyplot(fig2)
    else:
        st.info("No data available to plot growth trend.")

    # --- Students At Risk ---
    st.subheader("🚨 Students At Risk (Low Final RIT)")

    risk_cutoff = st.number_input(
        "Set RIT cutoff to identify 'At Risk' students:",
        min_value=100, max_value=300, value=200
    )

    at_risk_df = filtered_df[filtered_df["final_rit"] < risk_cutoff]

    if not at_risk_df.empty:
        st.write(f"⚠️ {len(at_risk_df)} student(s) identified below RIT {risk_cutoff}:")
        
        at_risk_df = at_risk_df.copy()
        at_risk_df["growth_needed"] = risk_cutoff - at_risk_df["final_rit"]
        
        st.dataframe(at_risk_df[["username", "grade_level", "final_rit", "growth_needed", "timestamp"]])

        st.download_button(
            label="📥 Download At-Risk Students as CSV",
            data=at_risk_df[["username", "grade_level", "final_rit", "growth_needed", "timestamp"]].to_csv(index=False).encode('utf-8'),
            file_name="at_risk_students.csv",
            mime="text/csv"
        )

    else:
        st.success(f"✅ No students below RIT {risk_cutoff} in current filters.")
