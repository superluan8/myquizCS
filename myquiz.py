import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import create_engine

# Create/connect SQLite database
engine = create_engine('sqlite:///quiz_results.db')

# Load CSV files
questions_df = pd.read_csv("questions.csv")   # Should have a column 'Question'
answers_df = pd.read_csv("anskey.csv")         # Should have answer choices as columns 'Option1', 'Option2', 'Option3', etc.
correct_df = pd.read_csv("keys.csv")           # Should have a column 'CorrectAnswer'

# Initialize session state
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.finished = False
    st.session_state.answered = False
    st.session_state.selected_option = None
    st.session_state.username = ""

st.title("🧠 Quiz App (CSV-based Questions and Answers)")

# Function to save result to SQLite
def save_result(username, final_score, total_questions):
    df = pd.DataFrame({
        "Username": [username],
        "Final_Score": [final_score],
        "Total_Questions": [total_questions],
        "Timestamp": [datetime.datetime.now()]
    })
    df.to_sql('quiz_results', con=engine, if_exists='append', index=False)
    st.success("✅ Your result has been saved to the database!")

# Function to create CSV for download
def download_result(username, final_score, total_questions):
    df = pd.DataFrame({
        "Username": [username],
        "Final_Score": [final_score],
        "Total_Questions": [total_questions],
        "Timestamp": [datetime.datetime.now()]
    })
    return df.to_csv(index=False).encode('utf-8')

# Quiz logic
if st.session_state.finished:
    st.success(f"🎉 Quiz completed! Your final score is {st.session_state.score} / {len(questions_df)}")

    st.subheader("📋 Save your result")
    st.session_state.username = st.text_input("Enter your name to save your result:")

    if st.button("Save Result"):
        if st.session_state.username.strip() != "":
            save_result(st.session_state.username, st.session_state.score, len(questions_df))
        else:
            st.warning("⚠️ Please enter your name before saving.")

    # CSV Download
    result_csv = download_result(st.session_state.username or "Student", st.session_state.score, len(questions_df))
    st.download_button(
        label="📥 Download My Result",
        data=result_csv,
        file_name="quiz_result.csv",
        mime="text/csv"
    )

    if st.button("Restart Quiz"):
        for key in ["q_index", "score", "finished", "answered", "selected_option", "username"]:
            st.session_state.pop(key, None)

else:
    # Get current question
    current_question = questions_df.iloc[st.session_state.q_index, 0]
    current_options = answers_df.iloc[st.session_state.q_index].dropna().tolist()  # Drop any empty choices
    correct_answer = correct_df.iloc[st.session_state.q_index, 0]

    st.subheader(f"Question {st.session_state.q_index + 1}:")
    st.write(current_question)

    # If not answered yet, show options
    if not st.session_state.answered:
        selected_text = st.radio("Choose your answer:", options=current_options)

        if st.button("Submit Answer"):
            if selected_text == correct_answer:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Incorrect! Correct answer was: {correct_answer}")
            st.session_state.answered = True
    else:
        # After answering, show "Next" button
        if st.button("Next Question ➡️"):
            st.session_state.q_index += 1
            st.session_state.answered = False
            st.session_state.selected_option = None
            if st.session_state.q_index >= len(questions_df):
                st.session_state.finished = True

# Sidebar with progress
st.sidebar.title("Quiz Progress")
st.sidebar.write(f"Score: {st.session_state.score}")
st.sidebar.write(f"Question {min(st.session_state.q_index + 1, len(questions_df))} of {len(questions_df)}")
