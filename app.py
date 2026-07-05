import asyncio
import streamlit as st

from interview_agent import InterviewAgent

st.set_page_config(
    page_title="AI Interview Preparation",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Interview Preparation System")
st.write("Practice technical interviews powered by Groq + Cognee")

# -----------------------------
# Session State
# -----------------------------

if "agent" not in st.session_state:
    st.session_state.agent = None

if "question" not in st.session_state:
    st.session_state.question = None

if "result" not in st.session_state:
    st.session_state.result = None


# -----------------------------
# Resume Input
# -----------------------------

resume = st.text_area(
    "Paste Your Resume",
    height=300
)

if st.button("Start Interview"):

    if resume.strip() == "":
        st.warning("Please paste your resume.")
        st.stop()

    st.session_state.agent = InterviewAgent(resume)

    with st.spinner("Generating Interview Question..."):

        st.session_state.question = asyncio.run(
            st.session_state.agent.generate_question()
        )

    st.success("Question Generated")


# -----------------------------
# Display Question
# -----------------------------

if st.session_state.question:

    q = st.session_state.question

    st.subheader("Interview Question")

    st.write(f"**Topic:** {q['topic']}")
    st.write(f"**Difficulty:** {q['difficulty']}")

    st.info(q["question"])

    answer = st.text_area(
        "Your Answer",
        height=220
    )

    if st.button("Submit Answer"):

        if answer.strip() == "":
            st.warning("Please write your answer.")
            st.stop()

        with st.spinner("Evaluating..."):

            result = asyncio.run(

                st.session_state.agent.evaluate_answer(

                    q["topic"],
                    q["question"],
                    answer

                )

            )

            asyncio.run(

                st.session_state.agent.update_memory(

                    q["topic"],
                    q["question"],
                    answer,
                    result

                )

            )

        st.session_state.result = result


# -----------------------------
# Result
# -----------------------------

if st.session_state.result:

    r = st.session_state.result

    st.header("Evaluation")

    st.metric(
        "Score",
        f"{r['score']}/10"
    )

    st.success(r["feedback"])

    st.subheader("Mistakes")

    if len(r["mistakes"]) == 0:

        st.write("No major mistakes.")

    else:

        for m in r["mistakes"]:

            st.write("•", m)

    st.subheader("Ideal Answer")

    st.write(r["ideal_answer"])


# -----------------------------
# Report
# -----------------------------

if st.session_state.agent:

    if st.button("Show Performance Report"):

        memory = st.session_state.agent.memory

        st.header("Performance Report")

        if len(memory["scores"]) == 0:

            st.info("No interview history.")

        else:

            for topic, scores in memory["scores"].items():

                avg = sum(scores) / len(scores)

                st.progress(avg / 10)

                st.write(
                    f"**{topic} : {avg:.2f}/10**"
                )

            st.subheader("Weak Topics")

            weak = st.session_state.agent.get_weak_topics()

            if weak:

                for t in weak:

                    st.error(t)

            else:

                st.success("No Weak Topics 🎉")
