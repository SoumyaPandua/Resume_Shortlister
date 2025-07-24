import os
import json
import re
import requests
import fitz  
from docx import Document  
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
load_dotenv()
 
 
class LLMResumeParser:
    def __init__(self, model_name=os.getenv("MODEL_NAME")):
        self.model = model_name
        self.client = InferenceClient(model=self.model, token=os.getenv("TOKEN"))
        self.system_prompt = self._build_system_prompt()
 
    def _build_system_prompt(self):
        return '''

You are an expert resume parser.
 
Your task is to extract structured data from unstructured resume text into exactly five predefined flat sections. You must return only one well-formed JSON object using the exact keys and definitions below. Do not add, omit, rename, or modify any section.
 
1. "skill"
Include only hard technical skills such as programming languages, frameworks, libraries, software tools, platforms, cloud services, or technical methodologies.
Do NOT include certifications, soft skills, role descriptions, degrees, or company names.
Examples: Python, TensorFlow, SQL, AWS, Docker, CI/CD, Agile, Power BI
 
2. "education"
Include only formal academic qualifications such as:
- Schooling (10th, 12th)
- Undergraduate (B.Tech, BSc)
- Postgraduate (M.Tech, MBA, MSc)
- Doctorate (PhD)
 
Each item must contain only the degree/program and institution name. Do NOT include years, CGPA, platforms like Coursera.
 
Examples:
- B.Tech in Computer Science from IIT Bombay
- 10th from Delhi Public School
- MBA from IIM Ahmedabad
 
3. "experience"
Each experience must be written as a single plain text string. Combine job title, company, location, and responsibilities into one sentence.
 
Example:
"Data Scientist at ABM, Nov22–Present — Developed SQL AI Agent using LangChain and Streamlit for natural language to SQL query conversion."
 
Do not use structured fields or key-value format.
 
4. "job role"
Include one specific job title that best represents the candidate’s most recent or primary designation.
Example:
- Data Scientist
 
5. "other information"
Include everything else:
- Certifications
- Soft skills
- Languages spoken
- Hobbies and interests
- Awards, objectives, extracurriculars
 
Certifications should go here regardless of provider.
 
Output Format:
{
  "skill": [],
  "education": [],
  "experience": [],
  "job role": [],
  "other information": []
}
 
Strict Rules:
- Use plain text list for each key
- Do NOT use nested objects or keys
- Do NOT hallucinate
- Do NOT wrap output in any explanation
'''
 
    def clean_text(self, text: str) -> str:
        # Clean and normalize text for LLM input
        text = text.replace('\n', '. ').replace('\r', '')
        text = text.replace('\\', ' or ')
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        text = re.sub(r'[\u200b-\u206f\u2e00-\u2e7f]', '', text)
        return re.sub(' +', ' ', text).strip()
 
    def extract_fields(self, resume_text: str) -> dict:
        cleaned_text = self.clean_text(resume_text)
       
        try:
           
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": cleaned_text}
            ]
           
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=None,
                temperature=0.0,
                top_p=1.0
            )
           
            # Extract the content from the response
            raw_output = response.choices[0].message.content.strip()
 
            print("\n Raw LLM Output:\n", raw_output)
 
            json_start = raw_output.find('{')
            json_end = raw_output.rfind('}')
            if json_start == -1 or json_end == -1:
                print(" Could not find valid JSON object in the LLM response.")
                return {}
 
            json_clean = raw_output[json_start:json_end+1]
 
            try:
                result = json.loads(json_clean)
            except json.JSONDecodeError as e:
                print(" JSON decoding failed:", e)
                return {}
 
            # Ensure all required keys are present
            required_keys = ["skill", "education", "experience", "job role", "other information"]
            for key in required_keys:
                if key not in result or not isinstance(result[key], list):
                    result[key] = []
 
            return result
 
        except Exception as e:
            print(f" Error calling or parsing LLM output: {e}")
            return {}
 
    def save_to_json(self, data: dict, output_dir: str, original_file: str):
        if not data or all(not v for v in data.values()):
            print(" Skipping save: No valid JSON returned.")
            return
 
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(original_file))[0]
        output_path = os.path.join(output_dir, f"{base_name}.json")
 
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f" Saved: {output_path}")
        except Exception as e:
            print(f" Failed to save {output_path}: {e}")
 
    def extract_text_from_file(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            try:
                doc = fitz.open(file_path)
                texts = []
                for page in doc:
                    text = page.get_text()
                    if not text.strip():
                        blocks = page.get_text("blocks")
                        text = "\n".join(
                            b[4].strip() for b in sorted(blocks, key=lambda b: (b[1], b[0])) if b[4].strip()
                        )
                    texts.append(text.strip())
                return " ".join(texts)
            except Exception as e:
                print(f" Error reading PDF {file_path}: {e}")
                return ""
        elif ext == ".docx":
            try:
                doc = Document(file_path)
                return " ".join(para.text.strip() for para in doc.paragraphs if para.text.strip())
            except Exception as e:
                print(f" Error reading DOCX {file_path}: {e}")
                return ""
        else:
            print(f"Unsupported file format: {file_path}")
            return ""
 
 
#  Clear old JSON files  
def clear_json_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(folder_path, filename)
                try:
                    os.remove(file_path)
                    print(f" Deleted old JSON: {file_path}")
                except Exception as e:
                    print(f" Could not remove file {file_path}: {e}")
    else:
        os.makedirs(folder_path)
 
 
#  Main resume parsing logic
def process_resumes(input_path: str, output_dir: str):
    parser = LLMResumeParser()
 
    clear_json_folder(output_dir)
 
    if os.path.isfile(input_path):
        files = [input_path] if input_path.lower().endswith((".pdf", ".docx")) else []
    elif os.path.isdir(input_path):
        files = [os.path.join(input_path, f) for f in os.listdir(input_path)
                 if f.lower().endswith((".pdf", ".docx"))]
    else:
        print(f" Invalid path: {input_path}")
        return
 
    for file_path in files:
        print(f"\n Processing: {file_path}")
        text = parser.extract_text_from_file(file_path)
        if not text.strip():
            print(f" Skipped empty or unreadable file: {file_path}")
            continue
        parsed = parser.extract_fields(text)
        parser.save_to_json(parsed, output_dir, file_path)