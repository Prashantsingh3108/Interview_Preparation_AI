import json
import os
from datetime import datetime

from llm.groq_client import ask_llm
from memory.cognee_memory import CogneeMemory


class InterviewAgent:

    def __init__(self, resume_text, memory_file="memory.json"):
        self.resume = resume_text
        self.memory_file = memory_file

        self.memory = self.load_memory()

        self.cognee = CogneeMemory()

   
    # Load Memory  
    def load_memory(self):

        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)

        return {
            "history": [],
            "weak_topics": {},
            "scores": {}
        }


    # Save Memory
    def save_memory(self):

        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=4)


    # Generate Question
    async def generate_question(self):

        context = await self.cognee.get_context_for_next_question()

        weak_topics = self.get_weak_topics()

        if weak_topics:
            focus = ", ".join(weak_topics)
        else:
            focus = "Python, Machine Learning, SQL"

        prompt = f"""
        You are a Senior Technical Interviewer.

        Candidate Resume:

        {self.resume}

        Previous Interview Context:

        {context}

        Weak Topics:

        {focus}

        Rules:

        1. Ask ONE interview question.
        2. Use the candidate's resume.
        3. Don't repeat previous questions.
        4. Difficulty should depend on previous performance.
        5. Return ONLY valid JSON.

        Example:

        {{
            "topic":"Python",
            "difficulty":"Medium",
            "question":"Explain the difference between List and Tuple in Python."
        }}
        """

        response = ask_llm(prompt)

        response = response.replace("```json", "")
        response = response.replace("```", "").strip()

        return json.loads(response)


    # Evaluate Answer
    async def evaluate_answer(
            self,
            topic,
            question,
            answer
    ):

        prompt = f"""
        You are an experienced technical interviewer.

        Question:

        {question}

        Candidate Answer:

        {answer}

        Evaluate the answer.

        Return ONLY JSON.

        {{
            "score":8,
            "feedback":"Good answer but improve examples.",
            "mistakes":[
                "Didn't mention time complexity",
                "No real-world example"
            ],
            "ideal_answer":"..."
        }}
        """

        response = ask_llm(prompt)

        response = response.replace("```json", "")
        response = response.replace("```", "").strip()

        return json.loads(response)


    # Update Memory
    async def update_memory(
            self,
            topic,
            question,
            answer,
            result
    ):

        record = {
            "time": str(datetime.now()),
            "topic": topic,
            "question": question,
            "answer": answer,
            "score": result["score"],
            "feedback": result["feedback"],
            "mistakes": result["mistakes"]
        }

        self.memory["history"].append(record)

        if topic not in self.memory["scores"]:
            self.memory["scores"][topic] = []

        self.memory["scores"][topic].append(result["score"])

        average = (
            sum(self.memory["scores"][topic])
            / len(self.memory["scores"][topic])
        )

        self.memory["weak_topics"][topic] = average

        self.save_memory()

        # Store in Cognee
        await self.cognee.add_interview_record(
            topic,
            question,
            answer,
            result["score"],
            result["feedback"],
            result["mistakes"]
        )


    # Weak Topics
    def get_weak_topics(self):

        weak = []

        for topic, avg in self.memory["weak_topics"].items():

            if avg < 7:
                weak.append(topic)

        return weak


    # Report


    def generate_report(self):

        print("\n========== INTERVIEW REPORT ==========\n")

        if not self.memory["scores"]:
            print("No interview history found.")
            return

        for topic, scores in self.memory["scores"].items():

            average = sum(scores) / len(scores)

            print(f"{topic}: {average:.2f}/10")

        print("\nWeak Topics:")

        weak = self.get_weak_topics()

        if weak:
            for topic in weak:
                print(f"• {topic}")
        else:
            print("None 🎉")