import json
import logging
import os
import re
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

# Core imports from your project architecture
from groq_client import ask_llm
from cognee_memory import CogneeMemory

# Configure production-ready logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="AI Interview Agent API",
    version="1.0.0",
    description="An intelligent async technical interview agent powered by Groq and Cognee."
)

class InterviewAgent:
    def __init__(self, resume_text: str, memory_file: str = "memory.json"):
        self.resume = resume_text
        self.memory_file = memory_file
        self.cognee = CogneeMemory()
        self.cognee_initialized = False
        self.memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load memory file: {e}")
        return {"history": [], "scores": {}, "weak_topics": {}}

    async def _init_cognee(self):
        if not self.cognee_initialized:
            try:
                await self.cognee.initialize()
                self.cognee_initialized = True
                logging.info("Cognee Cloud Connected Successfully.")
            except Exception as e:
                logging.error(f"Cognee Initialization Failed: {e}")

    def _parse_json_response(self, response: str, fallback: dict) -> dict:
        try:
            match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            clean_res = match.group(1).strip() if match else response.strip()
            return json.loads(clean_res)
        except Exception:
            logging.warning("Invalid JSON returned by LLM. Returning fallback structure.")
            return fallback

    def save_memory(self):
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.memory, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to write to memory file: {e}")

    def get_weak_topics(self):
        return [t for t, score in self.memory["weak_topics"].items() if score < 7]

    async def generate_question(self) -> dict:
        await self._init_cognee()
        try:
            context = await self.cognee.get_context_for_next_question()
        except Exception as e:
            logging.error(f"Error fetching Cognee context: {e}")
            context = "No previous interview context."

        weak_topics = self.get_weak_topics()
        focus = ", ".join(weak_topics) if weak_topics else "Python, SQL, Machine Learning"

        prompt = f"""You are a Senior Software Engineer interviewing a candidate.
Candidate Resume:\n{self.resume}\n
Previous Interview Memory:\n{context}\n
Weak Topics:\n{focus}\n
Instructions:
1. Ask exactly ONE question focusing on weak topics.
2. Never repeat previous questions.
3. Adjust difficulty dynamically (Increase if score > 8, Decrease if score < 5).
4. Return ONLY JSON matching this format: {{"topic":"Python", "difficulty":"Medium", "question":"..."}}"""

        # Run synchronous ask_llm in a worker thread to keep FastAPI fully non-blocking
        res = await asyncio.to_thread(ask_llm, prompt)
        return self._parse_json_response(res, {"topic": "General", "difficulty": "Medium", "question": res})

    async def evaluate_answer(self, topic: str, question: str, answer: str) -> dict:
        prompt = f"""You are an experienced technical interviewer.
Question:\n{question}\nCandidate Answer:\n{answer}\n
Evaluate the answer out of 10. Return ONLY JSON matching this format:
{{"score": 8, "feedback": "...", "mistakes": [], "ideal_answer": "..."}}"""

        res = await asyncio.to_thread(ask_llm, prompt)
        return self._parse_json_response(res, {"score": 5, "feedback": res, "mistakes": [], "ideal_answer": ""})

    async def update_memory(self, topic: str, question: str, answer: str, result: dict):
        record = {"time": str(datetime.now()), "topic": topic, "question": question, "answer": answer, **result}
        self.memory["history"].append(record)
        
        scores = self.memory["scores"].setdefault(topic, [])
        scores.append(result["score"])
        
        self.memory["weak_topics"][topic] = sum(scores) / len(scores)
        self.save_memory()

        await self._init_cognee()
        if self.cognee_initialized:
            try:
                await self.cognee.add_interview_record(topic, question, answer, result["score"], result["feedback"], result["mistakes"])
                logging.info("Interview record synchronized to Cognee.")
            except Exception as e:
                logging.error(f"Cognee Sync Error: {e}")

    def get_report_data(self) -> dict:
        if not self.memory["scores"]:
            return {"status": "No Interview History"}
        
        breakdown = {topic: round(sum(scores)/len(scores), 2) for topic, scores in self.memory["scores"].items()}
        return {
            "performance": breakdown,
            "weak_topics": self.get_weak_topics()
        }


# --- FASTAPI REQUEST/RESPONSE SCHEMAS ---

class InitializationPayload(BaseModel):
    resume: str

class AnswerPayload(BaseModel):
    topic: str
    question: str
    answer: str


# --- GLOBAL AGENT STATE MANAGEMENT ---
# Note: For production with multiple users, replace this global instantiation 
# with a database lookup or key-value cache (like Redis) keyed on a user ID token.
agent_instance: Optional[InterviewAgent] = None


@app.post("/interview/start", summary="Initialize or reset the interview with a resume")
async def start_interview(payload: InitializationPayload):
    global agent_instance
    agent_instance = InterviewAgent(resume_text=payload.resume)
    return {"message": "Interview session initialized successfully."}


@app.get("/interview/next-question", summary="Generate the next context-aware question")
async def get_next_question():
    if not agent_instance:
        raise HTTPException(status_code=400, detail="No active interview session. Call /interview/start first.")
    try:
        question_data = await agent_instance.generate_question()
        return question_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate question: {str(e)}")


@app.post("/interview/submit-answer", summary="Submit a candidate's answer for evaluation")
async def submit_answer(payload: AnswerPayload, background_tasks: BackgroundTasks):
    if not agent_instance:
        raise HTTPException(status_code=400, detail="No active interview session.")
    try:
        # Evaluate user answer asynchronously
        evaluation = await agent_instance.evaluate_answer(payload.topic, payload.question, payload.answer)
        
        # Save evaluation to local/cloud storage via Background Tasks so the candidate gets an instant response
        background_tasks.add_task(
            agent_instance.update_memory, 
            payload.topic, payload.question, payload.answer, evaluation
        )
        return evaluation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation pipeline failed: {str(e)}")


@app.get("/interview/report", summary="Retrieve a full summary of candidate performance")
async def get_report():
    if not agent_instance:
        raise HTTPException(status_code=400, detail="No active interview session.")
    return agent_instance.get_report_data()
