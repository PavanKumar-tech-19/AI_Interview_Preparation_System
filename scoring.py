import os
import json
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ---------------- AI ANSWER EVALUATION ---------------- #

def evaluate(question, answer):

    if not answer.strip():
        return {
            "score": 0,
            "strengths": "No answer provided.",
            "weaknesses": "Answer is empty.",
            "correct_answer": "Please answer the question.",
            "improvement_tips": "Write your answer in 2-3 sentences."
        }

    prompt = f"""
You are an expert technical interviewer.

Evaluate the candidate's answer.

Question:
{question}

Candidate Answer:
{answer}

Rules:
1. Score must be ONLY an integer between 0 and 10.
2. Strengths must be ONLY one short sentence.
3. Weaknesses must be ONLY one short sentence.
4. Correct Answer must be ONLY one short paragraph (maximum 40-50 words).
5. Do NOT use bullet points, numbering, code blocks, or lengthy explanations.
6. Improvement Tips must be ONLY one short sentence (maximum 15 words).
7. Return ONLY valid JSON in the format below.

Return ONLY this JSON:

{{
    "score": 0,
    "strengths": "",
    "weaknesses": "",
    "correct_answer": "",
    "improvement_tips": ""
}}
"""

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            text = response.text.strip()

            if text.startswith("```"):
                text = text.replace("```json", "").replace("```", "").strip()

            data = json.loads(text)

            score = max(0, min(int(data.get("score", 0)), 10))

            return {
                "score": score,
                "strengths": data.get("strengths", "Good attempt."),
                "weaknesses": data.get("weaknesses", "Needs improvement."),
                "correct_answer": data.get("correct_answer", "No answer available."),
                "improvement_tips": data.get("improvement_tips", "Practice more.")
            }

        except Exception as e:
            print(f"Attempt {attempt + 1}: {e}")

            if attempt < 2:
                time.sleep(3)

    # ---------- Fallback Evaluation ----------

    words = len(answer.split())

    if words >= 100:
        score = 9
    elif words >= 70:
        score = 8
    elif words >= 50:
        score = 7
    elif words >= 35:
        score = 6
    elif words >= 20:
        score = 5
    elif words >= 10:
        score = 4
    else:
        score = 3

    return {
        "score": score,
        "strengths": "Answer submitted successfully.",
        "weaknesses": "AI server is currently busy, so fallback evaluation was used.",
        "correct_answer": "The AI server is currently busy. Please try again later to view the ideal answer.",
        "improvement_tips": "Write clearer technical answers with key concepts."
    }

# ---------------- AI RESUME QUESTIONS ---------------- #

def generate_ai_resume_questions(resume_text):

    prompt =f"""
Read the following resume and generate 10 interview questions.

Resume:
{resume_text}

Return ONLY a JSON array.

Example:
[
"Question 1",
"Question 2",
"Question 3"
]
"""

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            text = response.text.strip()

            if text.startswith("```"):
                text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text)

        except Exception as e:
            print(f"Attempt {attempt+1}: {e}")

            if attempt < 2:
                time.sleep(3)

    return [
        "Tell me about yourself.",
        "Explain your final year project.",
        "Describe your technical skills.",
        "What programming languages do you know?",
        "Which technology are you most comfortable with?",
        "Describe a challenging problem you solved.",
        "What are your strengths?",
        "What are your weaknesses?",
        "Why should we hire you?",
        "Where do you see yourself in five years?"
    ]