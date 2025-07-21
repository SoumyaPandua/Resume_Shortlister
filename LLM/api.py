from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from main import main as run_pipeline
# import sys
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run-pipeline")
async def trigger_pipeline_from_uploads(
    jd: UploadFile = File(...),
    resumes: list[UploadFile] = File(...)
):
    try:
        temp_dir = tempfile.mkdtemp()
        resume_folder = os.path.join(temp_dir, "resumes")
        jd_folder = os.path.join(temp_dir, "jd")

        os.makedirs(resume_folder, exist_ok=True)
        os.makedirs(jd_folder, exist_ok=True)

        jd_path = os.path.join(jd_folder, jd.filename)
        with open(jd_path, "wb") as f:
            f.write(await jd.read())

        for resume in resumes:
            resume_path = os.path.join(resume_folder, resume.filename)
            with open(resume_path, "wb") as f:
                f.write(await resume.read())

        results = run_pipeline(resume_folder, jd_folder)

        return JSONResponse(content={"status": "success", "results": results}, status_code=200)

    except Exception as e:
        print("[ERROR] Pipeline failed:", e)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)