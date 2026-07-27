import json
import os
from config import client
from parser import get_jd, get_resumes

RESULTS_FILE = "ats_results.json"


def load_ats_results():
    if not os.path.exists(RESULTS_FILE):
        return None

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def handle_score_question(question):
    """Fast path: answer ATS-score questions straight from stored JSON."""

    results = load_ats_results()

    if not results:
        return "Run /analyze first to calculate ATS scores."

    scored = {
        name: data["score"]
        for name, data in results.items()
        if data.get("score") is not None
    }

    if not scored:
        return "Run /analyze first to calculate ATS scores."

    q = question.lower()

    if "highest" in q:
        best_file, best_score = max(scored.items(), key=lambda x: x[1])
        return f"🏆 Highest ATS Score\n\n{best_file}: {best_score}%"

    if "lowest" in q:
        worst_file, worst_score = min(scored.items(), key=lambda x: x[1])
        return f"📉 Lowest ATS Score\n\n{worst_file}: {worst_score}%"

    # General "what are the ats scores" style question
    lines = [f"{name}: {score}%" for name, score in scored.items()]
    return "📊 ATS Scores\n\n" + "\n".join(lines)


def answer_question(question):

    q = question.lower()

    if "ats score" in q or "ats scores" in q:
        return handle_score_question(question)

    jd = get_jd()
    resumes = get_resumes()

    if not resumes:
        return "❌ No resumes uploaded yet."

    resumes_text = ""
    for file_name, text in resumes:
        resumes_text += f"\n----- {file_name} -----\n{text}\n"

    jd_text = jd if jd else "No JD uploaded."

    prompt = f"""
You are an HR assistant answering questions about a job description and a set of uploaded resumes.

Answer ONLY using the information in the JD and resumes below. Refer to
candidates by their file name (or their name if it's clearly stated in the resume).

If the answer isn't present in the documents, say:
"I couldn't find that information in the uploaded files."

Job Description:
{jd_text}

Resumes:
{resumes_text}

Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are an HR assistant that answers questions strictly from provided resume and JD text.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"[qa.py error] {e}")
        return "⚠️ Sorry, I ran into an error answering that. Try rephrasing or ask again."