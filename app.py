import asyncio
import streamlit as st

from agents.interview_agent import InterviewAgent

# --------------------------------
# Page Configuration
# --------------------------------
st.set_page_config(
    page_title="AI Interview Preparation",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Interview Preparation System")
st.write("Powered by **Groq + Cognee**")

# --------------------------------
# Load Resume
# --------------------------------

try:
    with open("resume/resume.txt", "r", encoding="utf-8") as f:
        resume = f.read()
except FileNotFoundError:
    st.error("resume/resume.txt not found.")
    st.stop()

agent = InterviewAgent(resume)

# --------------------------------
# Session State
# --------------------------------

if "question" not in st.session_state:
    st.session_state.question = None

if "result" not in st.session_state:
    st.session_state.result = None

# --------------------------------
# Generate Question
# --------------------------------

if st.button("Generate Interview Question"):

    with st.spinner("Generating interview question..."):

        try:
            st.session_state.question = asyncio.run(
                agent.generate_question()
            )

        except Exception as e:
            st.error(f"Error : {e}")

# --------------------------------
# Show Question
# --------------------------------

if st.session_state.question:

    st.subheader("Interview Question")

    st.info(st.session_state.question["question"])

    answer = st.text_area(
        "Write your answer",
        height=250
    )

    if st.button("Submit Answer"):

        if answer.strip() == "":
            st.warning("Please enter your answer.")
        else:

            with st.spinner("Evaluating..."):

                try:

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

                except Exception as e:

                    st.error(f"Evaluation Error : {e}")

# --------------------------------
# Feedback
# --------------------------------

if st.session_state.result:

    st.divider()

    st.header("Interview Result")

    st.metric(
        "Score",
        f"{st.session_state.result['score']}/10"
    )

    st.subheader("Feedback")

    st.success(
        st.session_state.result["feedback"]
    )

    st.subheader("Mistakes")

    if st.session_state.result["mistakes"]:

        for mistake in st.session_state.result["mistakes"]:
            st.write("•", mistake)

    else:

        st.success("No mistakes found.")

    st.subheader("Ideal Answer")

    st.write(st.session_state.result["ideal_answer"])

# --------------------------------
# Progress Report
# --------------------------------

st.divider()

if st.button("Show Progress Report"):

    st.header("Progress Report")

    if not agent.memory["scores"]:

        st.warning("No Interview History Found.")

    else:

        for topic, scores in agent.memory["scores"].items():

            average = sum(scores) / len(scores)

            st.write(f"### {topic}")

            st.progress(min(average / 10, 1.0))

            st.write(f"Average Score : {average:.2f}/10")

        weak = agent.get_weak_topics()

        st.subheader("Weak Topics")

        if weak:

            for topic in weak:

                st.write("•", topic)

        else:

            st.success("No Weak Topics 🎉")