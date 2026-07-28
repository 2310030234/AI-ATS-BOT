from config import client

def analyze_resume(jd, resume):

    prompt = f"""
You are an expert ATS (Applicant Tracking System).

Compare the following Job Description and Resume.

IMPORTANT: Do not show your reasoning, thinking process, or analysis steps.
Do not explain how you calculated anything. Output ONLY the final result in
EXACTLY this format and nothing else:

🏆 ATS Score: xx%

🟢 Hiring Decision:
Strong Hire / Consider / Reject

✅ Matching Skills
- Skill 1
- Skill 2
- Skill 3

❌ Missing Skills
- Skill 1
- Skill 2

💡 Suggestions
- Suggestion 1
- Suggestion 2
- Suggestion 3

Job Description:
{jd}

Resume:
{resume}
"""

    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are an ATS Resume Analyzer. You output ONLY the final formatted result, never your reasoning or intermediate steps."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        if not response or not response.choices:
            print(f"[ats.py] Empty response from API: {response}")
            return "⚠️ ATS analysis failed for this resume (no response from AI model). Please try /analyze again."

        return response.choices[0].message.content

    except Exception as e:
        print(f"[ats.py error] {e}")
        return "⚠️ ATS analysis failed for this resume due to an error. Please try /analyze again."