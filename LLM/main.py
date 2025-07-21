import os
import time
import traceback
from extraction.resume_extraction import process_resumes as extract_all_resumes
from extraction.jd_extraction import process_jds as extract_all_jds
from embedding.resume_embedding import embed_all_jsons_from_folder as embed_resumes
from embedding.jd_embedding import embed_all_jsons_from_folder as embed_jds
from compare.llm import main as run_llm_comparison

def timed_step(step_name, func, *args, **kwargs):
    print(f"\n[STEP] {step_name}...")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        print(f"[DONE] {step_name} in {time.time() - start:.2f}s")
        return result
    except Exception as e:
        print(f"[ERROR] {step_name} failed: {e}")
        traceback.print_exc()
        return None

def main(resume_folder, jd_folder):
    print("\n=== Starting Resume Shortlisting Pipeline ===")

    resume_json = os.path.join(resume_folder, "json_resume")
    jd_json = os.path.join(jd_folder, "json_jd")

    chroma_resume = os.path.join(resume_folder, "chroma_resume")
    chroma_jd = os.path.join(jd_folder, "chroma_jd")

    os.makedirs(resume_json, exist_ok=True)
    os.makedirs(jd_json, exist_ok=True)
    os.makedirs(chroma_resume, exist_ok=True)
    os.makedirs(chroma_jd, exist_ok=True)

    timed_step("Resume Extraction", extract_all_resumes, resume_folder, resume_json)
    timed_step("JD Extraction", extract_all_jds, jd_folder, jd_json)
    timed_step("Resume Embedding", embed_resumes, resume_json, chroma_resume)
    timed_step("JD Embedding", embed_jds, jd_json, chroma_jd)

    results = timed_step("LLM-Based Comparison", run_llm_comparison, chroma_resume, chroma_jd)
    print("[RESULTS] LLM Comparison Results:")
    if results:
        for result in results:
            print(result)
            print("-" * 100)
    print("\n=== Pipeline Completed ===")
    if not results or not isinstance(results, list):
        raise RuntimeError("LLM did not return valid results")

    return results