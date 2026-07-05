import json
import logging
import os
from datetime import datetime

from llm.groq_client import ask_llm
from memory.cognee_memory import CogneeMemory


logging.basicConfig(level=logging.INFO)


class InterviewAgent:

    def __init__(self, resume_text, memory_file="memory.json"):

        self.resume = resume_text
        self.memory_file = memory_file

        self.memory = self.load_memory()

        self.cognee = CogneeMemory()

        self.cognee_initialized = False


    # Initialize Cognee Cloud


    async def initialize_cognee(self):

        if not self.cognee_initialized:

            try:

                await self.cognee.initialize()
                await self.cognee.get_context_for_question()
                await self.cognee.add_interview_record(...)

                self.cognee_initialized = True

                logging.info("Cognee Connected")

            except Exception as e:

                logging.error(f"Cognee Initialization Failed : {e}")


    # Load Memory


    def load_memory(self):

        if os.path.exists(self.memory_file):

            with open(self.memory_file, "r") as f:

                return json.load(f)

        return {

            "history": [],

            "scores": {},

            "weak_topics": {}

        }


    # Save Memory
    def save_memory(self):

        with open(self.memory_file, "w") as f:

            json.dump(self.memory, f, indent=4)


    # Generate Interview Question
    async def generate_question(self):

        await self.initialize_cognee()

        try:

            context = await self.cognee.get_context_for_next_question()

        except Exception as e:

            logging.error(e)

            context = "No previous interview context."

        weak_topics = self.get_weak_topics()

        focus = ", ".join(weak_topics) if weak_topics else \
            "Python, SQL, Machine Learning"

        prompt = f"""

You are a Senior Software Engineer interviewing a candidate.

Candidate Resume

{self.resume}

Previous Interview Memory

{context}

Weak Topics

{focus}

Instructions

1. Ask exactly ONE question.
2. Never repeat previous questions.
3. Focus on weak topics.
4. Increase difficulty if candidate scored above 8.
5. Reduce difficulty if candidate scored below 5.
6. Return ONLY JSON.

Output

{{
"topic":"Python",
"difficulty":"Medium",
"question":"Explain generators in Python."
}}

"""

        response = ask_llm(prompt)

        response = response.replace("```json", "").replace("```", "").strip()

        try:

            return json.loads(response)

        except Exception:

            logging.warning("Invalid JSON returned by LLM.")

            return {

                "topic": "General",

                "difficulty": "Medium",

                "question": response

            }

    # Evaluate Answer
    async def evaluate_answer(

            self,

            topic,

            question,

            answer

    ):

        prompt = f"""

You are an experienced technical interviewer.

Question

{question}

Candidate Answer

{answer}

Evaluate the answer.

Give score out of 10.

Return ONLY JSON.

{{
"score":8,
"feedback":"Good explanation.",
"mistakes":["No examples"],
"ideal_answer":"..."
}}

"""

        response = ask_llm(prompt)

        response = response.replace("```json", "").replace("```", "").strip()

        try:

            return json.loads(response)

        except Exception:

            return {

                "score":5,

                "feedback":response,

                "mistakes":[],

                "ideal_answer":""

            }


    # Update Memory
    async def update_memory(

            self,

            topic,

            question,

            answer,

            result

    ):

        record = {

            "time":str(datetime.now()),

            "topic":topic,

            "question":question,

            "answer":answer,

            "score":result["score"],

            "feedback":result["feedback"],

            "mistakes":result["mistakes"]

        }

        self.memory["history"].append(record)

        if topic not in self.memory["scores"]:

            self.memory["scores"][topic] = []

        self.memory["scores"][topic].append(result["score"])

        average = sum(

            self.memory["scores"][topic]

        ) / len(

            self.memory["scores"][topic]

        )

        self.memory["weak_topics"][topic] = average

        self.save_memory()

        await self.initialize_cognee()

        try:

            await self.cognee.add_interview_record(

                topic,

                question,

                answer,

                result["score"],

                result["feedback"],

                result["mistakes"]

            )

            logging.info("Interview stored in Cognee")

        except Exception as e:

            logging.error(f"Cognee Error : {e}")


    # Weak Topics    def get_weak_topics(self):

        return [

            topic

            for topic, score

            in self.memory["weak_topics"].items()

            if score < 7

        ]


    # Report
    def generate_report(self):

        print("\n========== REPORT ==========\n")

        if not self.memory["scores"]:

            print("No Interview History")

            return

        for topic, scores in self.memory["scores"].items():

            avg = sum(scores) / len(scores)

            print(f"{topic:<20}{avg:.2f}/10")

        print("\nWeak Topics")

        weak = self.get_weak_topics()

        if weak:

            for t in weak:

                print("•", t)

        else:

            print("None 🎉")