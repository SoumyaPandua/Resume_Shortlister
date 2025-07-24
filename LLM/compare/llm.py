import os
import json
import re
import time
from chromadb import PersistentClient
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
load_dotenv()

# Constants
HF_TOKEN = os.getenv("TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME")
FIELD_ORDER = ["Skills", "Education", "Experience", "Job Role"]

# Initialize clients
llm_client = InferenceClient(model=MODEL_NAME, token=HF_TOKEN)

# Prompt Templates
system_prompt = """
You are a world-class HR, Talent Acquisition, and Generative AI Specialist with deep expertise in job-role alignment, semantic document comparison, and hiring decision automation.
 
You are tasked with comparing a candidate resume and a job description. Both are pre-parsed into structured fields: Skills, Education, Job Role, Experience, and Other Information. Your job is to assess the alignment strictly based on meaning — not exact keyword matches.
 
You must return a single valid JSON object in the structure described below.
 
Instructions:
Evaluate semantic relevance, not just keyword overlap. For example, treat "ML Engineer" and "Machine Learning Engineer" as identical.
 
Use real-world hiring logic: If a resume exceeds the JD requirements (e.g., more skills, more education, deeper experience), the match_pct should be high — even 100%.
 
Avoid over-penalizing minor differences. Focus on capability and fit.
 
NEVER hallucinate or infer information not explicitly present in either document.
 
NEVER nest objects inside any field — your output must remain a flat JSON.
 
Explanations must be insightful, human-readable, and professional — written as if speaking to a hiring manager.
 
Escape any invalid characters like tabs/newlines using \\t and \\n.
 
Do not include any commentary or text outside the JSON.
 
Always use consistent phrasing and structure in your explanations across different runs. Do not rephrase or creatively rewrite unless required. Match explanations must be templated and repeatable.
 
Never vary the field names or key order. Output only the structured JSON.
 
If fields are missing or partially present in either resume or JD, evaluate based on available data and explain any impact on match_pct clearly.
 
Field Matching Logic:
Skills
 
Match based on technical equivalence.
 
If the resume includes all required skills or more, assign 100%.
 
If semantically similar (e.g., "pandas" vs. "data manipulation in Python"), assign high match_pct (80–95%).
 
Penalize only if key required skills are missing or unrelated.
 
Education
 
If the candidate’s education meets or exceeds the JD’s degree level and is in a relevant field, assign 100% match.
 
Example: JD asks for “B Tech / M Tech in Computer/IT” — if the candidate has an M.Tech in CSE or Data Science and a B.E. in Computer Science, this is a perfect match (100%).
 
If the candidate has both Bachelor’s and Master’s degrees in related technical fields (Computer Science, IT, Data Science, AI, etc.), assign 100%.
 
Slight title variations (e.g., “B.E.” instead of “B.Tech”) are acceptable.
 
Reduce score when:
 
Degree is in a different domain (e.g., Civil, Mechanical, Marketing).
 
Degree level is lower than required (e.g., only Diploma when JD asks for B.Tech).
 
Field of study is unrelated (assign low score, e.g., <30%).
 
Recognize institution reputation lightly but avoid harsh penalties unless irrelevant.
 
Explain clearly why any penalty applies.
 
Experience
 
Match on role relevance, technologies used, domain familiarity, and years of experience.
 
Experience meeting or exceeding JD expectations should score high (90–100%).
 
Penalize gaps or mismatches, with explanation.
 
Job Role
 
Normalize semantically equivalent titles (e.g., "ML Engineer" = "Machine Learning Engineer").
 
Exact matches to any JD title get 100%.
 
Semantically aligned roles (e.g., “Data Scientist” vs. “ML Engineer”) get high score (90–95%).
 
Overlapping domains (Data Scientist, ML Engineer, Generative AI Engineer) should be considered closely.
 
Penalize clear role mismatches (e.g., “Project Manager” vs. “ML Engineer”) with clear explanation.
 
Prioritize AI/ML/Generative AI domain relevance over exact wording.
 
OverallMatchPercentage
 
Weighted heavily by Skills, Experience, Education, and Job Role (suggested weights: Skills 35%, Experience 30%, Education 20%, Job Role 15%).
 
Other Information can add or subtract minor bonus/penalty (±5%).
 
Clearly explain overall score rationale in simple terms.
 
AI_Generated_Estimate_Percentage
 
Estimate likelihood resume is AI-generated based on repetitive phrasing, unnatural tone, excessive perfection, or generic language.
 
Example Reasoning (Chain-of-Thought):
Skills:
JD requires Python, Machine Learning, Pandas. Resume lists Python programming, Data manipulation in Python, ML model development.
 
"Python programming" exactly matches "Python" → full match.
 
"Data manipulation in Python" semantically matches "Pandas" → high similarity (~90%).
 
"ML model development" maps to "Machine Learning" → direct match.
 
All required skills are covered, some with semantic variation.
Conclusion: 100% match; candidate meets or exceeds all JD skills.
Explanation: The candidate’s skills fully cover the JD’s required skills with slight semantic differences, demonstrating strong technical equivalence and exceeding expectations.
 
Education:
JD requires “B Tech / M Tech in Computer Science or IT”. Resume has “M.Tech in Data Science” and “B.E. in Computer Science”.
 
Do not assign 0% unless the degree is both at the wrong level and in an unrelated field.
 
Degrees exceed requirements.
 
Fields are relevant and closely related.
Conclusion: 100% match.
Explanation: Candidate holds advanced degrees in directly related fields, fully satisfying and exceeding JD educational requirements.
 
Experience:
JD needs 3+ years in ML model deployment. Resume shows 5 years in ML engineering with deployment projects using similar technologies.
Conclusion: 100% match.
Explanation: Candidate’s experience exceeds JD requirements in duration and domain expertise.
 
Job Role:
JD title: “Machine Learning Engineer”. Resume title: “ML Engineer”.
 
Titles semantically identical.
Conclusion: 100% match.
Explanation: The roles align perfectly; both represent the same position despite wording differences.
 
Output Format (strict):
{
"{resume_filename}": {
"Skills": {
"match_pct": float,
"resume_value": string,
"job_description_value": string,
"explanation": string
},
"Education": {
"match_pct": float,
"resume_value": string,
"job_description_value": string,
"explanation": string
},
"Job Role": {
"match_pct": float,
"resume_value": string,
"job_description_value": string,
"explanation": string
},
"Experience": {
"match_pct": float,
"resume_value": string,
"job_description_value": string,
"explanation": string
},
"OverallMatchPercentage": float,
"why_overall_match_is_this": string,
"AI_Generated_Estimate_Percentage": float
}
}
 
Return ONLY the JSON object. No extra comments or explanation.
"""

user_prompt_template = """
You are tasked with comparing a candidate’s resume and a job description, each parsed into structured fields: Skills, Education, Job Role, Experience, and Other Information.
 
Your goal is to evaluate the semantic alignment between the resume and the job description — focusing on meaning and capability, not exact keyword matches.
 
Return only a single valid JSON object in this exact structure (replace {resume_filename} with the actual resume file name):
 
json
Copy
Edit
{{
  "{resume_filename}": {{
    "Skills": {{
      "match_pct": float,
      "resume_value": string,
      "job_description_value": string,
      "explanation": string
    }},
    "Education": {{
      "match_pct": float,
      "resume_value": string,
      "job_description_value": string,
      "explanation": string
    }},
    "Job Role": {{
      "match_pct": float,
      "resume_value": string,
      "job_description_value": string,
      "explanation": string
    }},
    "Experience": {{
      "match_pct": float,
      "resume_value": string,
      "job_description_value": string,
      "explanation": string
    }},
    "OverallMatchPercentage": float,
    "why_overall_match_is_this": string,
    "AI_Generated_Estimate_Percentage": float
  }}
}}
Evaluation Instructions:
Semantic similarity means matching based on meaning, not exact text. For example, treat "ML Engineer" and "Machine Learning Engineer" as equivalent.
 
Use realistic hiring logic: if the resume exceeds JD requirements (more skills, higher education, deeper experience), assign high or full match_pct.
 
Assign match_pct scores from 0 to 100 representing the degree of semantic alignment.
 
Use these weighting guidelines to calculate OverallMatchPercentage:
 
Skills: 35%
 
Experience: 30%
 
Education: 20%
 
Job Role: 15%
 
Other Information may add or subtract up to ±5% from the overall score.
 
Avoid penalizing minor wording or formatting differences.
 
Penalize missing key required fields appropriately.
 
No semicolons (;) in values — use periods or commas
 
For missing or partial data in any field, explain clearly how it impacts match_pct.
 
Do not hallucinate or infer data not explicitly present in either document.
 
Never nest JSON objects inside any field values; keep all fields flat.
 
Escape special characters (tabs, newlines, quotes) using \\t, \\n, \" respectively.
 
Maintain consistent phrasing and tone in explanations, as if writing to a hiring manager.
 
Do not output any text or commentary outside the JSON object.
 
Chain-of-Thought Reasoning Examples:
Skills:
JD requires Python, Machine Learning, Pandas. Resume lists Python programming, Data manipulation in Python, ML model development.
 
"Python programming" = "Python" → 100% match.
 
"Data manipulation in Python" semantically equals "Pandas" → ~90% match.
 
"ML model development" matches "Machine Learning" → 100%.
Result: 100% match_pct since all key skills are met or exceeded.
Explanation: Candidate’s skills fully cover the JD’s requirements, showing strong semantic equivalence and exceeding expectations.
 
Education:
JD requires “B Tech / M Tech in Computer Science or IT”. Resume has “M.Tech in Data Science” and “B.E. in Computer Science”.
 
Degrees meet or exceed requirements and are relevant.
Result: 100% match_pct.
Explanation: Candidate’s advanced degrees in closely related fields fully satisfy JD educational requirements.
 
Experience:
JD requires 3+ years in ML model deployment. Resume has 5 years of ML engineering with similar deployment projects.
Result: 100% match_pct.
Explanation: Candidate’s experience surpasses JD expectations in both duration and domain expertise.
 
Job Role:
JD title: “Machine Learning Engineer”. Resume title: “ML Engineer”.
 
Titles are semantically equivalent.
Result: 100% match_pct.
Explanation: Roles align perfectly despite wording differences.
 
Output:
Return only the JSON object following the structure above. Do not add any extra text or commentary.
"""

def get_collection_docs(client, collection_name):
    try:
        collection = client.get_collection(collection_name)
        results = collection.get(include=["documents"])
        docs = results.get("documents", [])
        if docs and isinstance(docs[0], list):
            docs = [d for sublist in docs for d in sublist]
        return docs
    except Exception as e:
        print(f"[ERROR] Failed to load collection '{collection_name}': {e}")
        return []

def build_field_texts(field_names, docs):
    lines = []
    for name, doc in zip(field_names, docs):
        doc_clean = re.sub(rf"^{re.escape(name)}:\s*", "", doc, flags=re.IGNORECASE)
        lines.append(f"{name}: {doc_clean}")
    return "\n".join(lines)

def clean_llm_json(raw_response):
    raw = raw_response.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    brace_stack = []
    start_idx = None
    for i, char in enumerate(raw):
        if char == '{':
            if start_idx is None:
                start_idx = i
            brace_stack.append('{')
        elif char == '}':
            if brace_stack:
                brace_stack.pop()
                if not brace_stack:
                    return raw[start_idx:i+1].strip()
    return raw

def normalize_llm_response(data):
    for field in ["Skills", "Education", "Job Role", "Experience"]:
        if field in data:
            for key in ["resume_value", "job_description_value"]:
                value = data[field].get(key)
                if isinstance(value, list):
                    data[field][key] = ", ".join(map(str, value))
    return data

def query_llm(system_prompt, user_prompt, retries=2):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    for attempt in range(retries):
        try:
            response = llm_client.chat_completion(messages=messages, max_tokens=2048, temperature=0.0, top_p=1.0, stop=["```"])
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] LLM call failed (attempt {attempt+1}): {e}")
            time.sleep(1)
    return ""

def main(resume_db_path, jd_db_path):
    try:
        start_time = time.time()
        
        jd_client = PersistentClient(path=jd_db_path)
        resume_client = PersistentClient(path=resume_db_path)

        # Get all collections (each collection represents one JD or resume)
        jd_collections = [c.name for c in jd_client.list_collections()]
        resume_collections = [c.name for c in resume_client.list_collections()]

        if not jd_collections or not resume_collections:
            raise ValueError("No collections found in the provided database paths")

        all_results = []

        for jd_collection in jd_collections:
            jd_docs = get_collection_docs(jd_client, jd_collection)
            if len(jd_docs) < 5:
                continue

            jd_text = build_field_texts(FIELD_ORDER, jd_docs[:4])
            jd_other_info = jd_docs[4] if len(jd_docs) > 4 else ""

            for resume_collection in resume_collections:
                resume_docs = get_collection_docs(resume_client, resume_collection)
                if len(resume_docs) < 5:
                    continue

                resume_text = build_field_texts(FIELD_ORDER, resume_docs[:4])
                resume_other_info = resume_docs[4] if len(resume_docs) > 4 else ""

                comparison_name = f"{resume_collection}_vs_{jd_collection}"

                user_prompt = user_prompt_template.format(resume_filename=comparison_name)
                user_prompt += f"\n\nJob Description Other Information:\n{jd_other_info}"
                user_prompt += f"\nResume Other Information:\n{resume_other_info}"
                user_prompt += f"\n\nJob Description:\n{jd_text}\n\nResume:\n{resume_text}"

                raw = query_llm(system_prompt, user_prompt)
                if not raw:
                    continue

                try:
                    cleaned = clean_llm_json(raw)
                    parsed = json.loads(cleaned)
                    parsed = {k: normalize_llm_response(v) for k, v in parsed.items()}
                    all_results.append(parsed)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to parse JSON response for {comparison_name}: {e}")
                    continue
                except Exception as e:
                    print(f"[ERROR] Processing response for {comparison_name}: {e}")
                    continue

        if not all_results:
            raise ValueError("No valid comparisons were generated")

        print(f"\n[INFO] Total time: {time.time() - start_time:.2f} sec")
        return all_results

    except Exception as e:
        print(f"[ERROR] In main comparison function: {e}")
        return []