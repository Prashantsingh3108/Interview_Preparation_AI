import json
import os


class ReportGenerator:

    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file

    # -----------------------------
    # Load Memory
    # -----------------------------
    def load_memory(self):

        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)

        return {
            "history": [],
            "scores": {},
            "weak_topics": {}
        }

    # -----------------------------
    # Generate Report
    # -----------------------------
    def generate_report(self):

        memory = self.load_memory()

        if not memory["scores"]:

            return {
                "overall_score": 0,
                "total_questions": 0,
                "best_topic": None,
                "worst_topic": None,
                "weak_topics": [],
                "topic_scores": {}
            }

        topic_scores = {}

        all_scores = []

        for topic, scores in memory["scores"].items():

            avg = sum(scores) / len(scores)

            topic_scores[topic] = round(avg, 2)

            all_scores.extend(scores)

        overall_score = round(

            sum(all_scores) / len(all_scores),

            2

        )

        total_questions = len(memory["history"])

        best_topic = max(

            topic_scores,

            key=topic_scores.get

        )

        worst_topic = min(

            topic_scores,

            key=topic_scores.get

        )

        weak_topics = [

            topic

            for topic, score in topic_scores.items()

            if score < 7

        ]

        return {

            "overall_score": overall_score,

            "total_questions": total_questions,

            "best_topic": best_topic,

            "worst_topic": worst_topic,

            "weak_topics": weak_topics,

            "topic_scores": topic_scores

        }

    # -----------------------------
    # Print Report
    # -----------------------------
    def print_report(self):

        report = self.generate_report()

        print("\n========== INTERVIEW REPORT ==========\n")

        print(f"Overall Score : {report['overall_score']}/10")

        print(f"Total Questions : {report['total_questions']}")

        print(f"Best Topic : {report['best_topic']}")

        print(f"Worst Topic : {report['worst_topic']}")

        print("\nTopic-wise Scores\n")

        for topic, score in report["topic_scores"].items():

            print(f"{topic} : {score}/10")

        print("\nWeak Topics")

        if report["weak_topics"]:

            for topic in report["weak_topics"]:

                print(f"• {topic}")

        else:

            print("None 🎉")