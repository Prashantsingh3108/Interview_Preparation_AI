import asyncio
import streamlit as st

from agents.interview_agent import InterviewAgent
from report import ReportGenerator

# ---------------------------------------------------
# Page Configuration
# ---------------------------------------------------

st.set_page_config(
    page_title="AI Interview Preparation",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Interview Preparation System")

st.markdown(
    """
Practice technical interviews using **Groq + Cognee Memory**.

The system remembers previous interviews and asks smarter questions.
"""
)

# ---------------------------------------------------
# Load Resume
# ---------------------------------------------------

try:

    with open("resume/resume.txt", "r", encoding="utf-8") as f:

        resume = f.read()

except FileNotFoundError:

    st.error("resume/resume.txt not found.")

    st.stop()

# ---------------------------------------------------
# Create Agent
# ---------------------------------------------------

agent = InterviewAgent(resume)

# ---------------------------------------------------
# Session State
# ---------------------------------------------------

if "question" not in st.session_state:
    st.session_state.question = None

if "result" not in st.session_state:
    st.session_state.result = None

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------

with st.sidebar:

    st.header("Interview Settings")

    st.success("Groq Connected")

    st.success("Cognee Memory Enabled")

    if st.button("Show Progress Report"):

        report = ReportGenerator().generate_report()

        st.subheader("Overall")

        st.metric(
            "Overall Score",
            f"{report['overall_score']}/10"
        )

        st.metric(
            "Questions",
            report["total_questions"]
        )

        st.write("### Best Topic")

        st.success(report["best_topic"])

        st.write("### Weak Topics")

        if report["weak_topics"]:

            for topic in report["weak_topics"]:

                st.warning(topic)

        else:

            st.success("No weak topics")

        st.write("### Topic Scores")

        for topic, score in report["topic_scores"].items():

            st.progress(score / 10)

            st.write(f"{topic}: {score}/10")

# ---------------------------------------------------
# Generate Question
# ---------------------------------------------------

col1, col2 = st.columns([1, 1])

with col1:

    if st.button(
        "🎯 Generate Interview Question",
        use_container_width=True
    ):

        with st.spinner("Generating Question..."):

            st.session_state.question = asyncio.run(
                agent.generate_question()
            )

            st.session_state.result = None

# ---------------------------------------------------
# Show Question
# ---------------------------------------------------

if st.session_state.question:

    st.divider()

    st.subheader("Interview Question")

    st.info(
        st.session_state.question["question"]
    )

    answer = st.text_area(
        "Write your answer",
        height=250
    )

    if st.button(
        "Submit Answer",
        use_container_width=True
    ):

        if answer.strip() == "":

            st.warning("Please write your answer.")

        else:

            with st.spinner("Evaluating..."):

                result = asyncio.run(

                    agent.evaluate_answer(

                        st.session_state.question["topic"],

                        st.session_state.question["question"],

                        answer

                    )

                )

                asyncio.run(

                    agent.update_memory(

                        st.session_state.question["topic"],

                        st.session_state.question["question"],

                        answer,

                        result

                    )

                )

                st.session_state.result = result

# ---------------------------------------------------
# Result
# ---------------------------------------------------

if st.session_state.result:

    st.divider()

    st.header("Evaluation")

    st.metric(
        "Score",
        f"{st.session_state.result['score']}/10"
    )

    st.success(
        st.session_state.result["feedback"]
    )

    st.subheader("Mistakes")

    if st.session_state.result["mistakes"]:

        for mistake in st.session_state.result["mistakes"]:

            st.error(mistake)

    else:

        st.success("Excellent Answer")

    st.subheader("Ideal Answer")

    st.info(
        st.session_state.result["ideal_answer"]
    )