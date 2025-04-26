import streamlit as st
import pandas as pd

# Load CSV files
questions_df = pd.read_csv("questions.csv")   # Should have a column 'Question'
answers_df = pd.read_csv("anskey.csv")        # Should have answer choices as columns 'Option1', 'Option2', 'Option3', etc.
correct_df = pd.read_csv("keys.csv")         # Should have a column 'CorrectAnswer'

# Initialize session state
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.finished = False
    st.session_state.answered = False
    st.session_state.selected_option = None

st.title("🧠 Quiz App (CSV-based Questions and Answers)")

# Check if quiz is finished
if st.session_state.finished:
    st.success(f"Quiz completed! Your final score is {st.session_state.score}/{len(questions_df)}")
    if st.button("Restart Quiz"):
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.finished = False
        st.session_state.answered = False
        st.session_state.selected_option = None
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
