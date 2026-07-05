from flask import Flask, request, jsonify

from interview_agent import InterviewAgent

app = Flask(__name__)

# Load resume once when the server starts
try:
    with open("resume.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
except FileNotFoundError:
    resume_text = ""

agent = InterviewAgent(resume_text=resume_text)


@app.route("/")
def home():
    return {
        "message": "Interview Preparation AI API is running.",
        "status": "success"
    }


@app.route("/question", methods=["GET"])
def get_question():
    try:
        question = agent.generate_question()
        return jsonify({
            "question": question
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/answer", methods=["POST"])
def evaluate_answer():
    try:
        data = request.get_json()

        question = data.get("question")
        answer = data.get("answer")

        feedback = agent.evaluate_answer(question, answer)

        return jsonify({
            "feedback": feedback
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/report", methods=["GET"])
def report():
    try:
        report = agent.generate_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)