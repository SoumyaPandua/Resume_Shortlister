import { prisma } from '@/db';
import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import { v4 as uuid } from 'uuid';
import axios from 'axios';
import sendEmail from '@/lib/sendEmail';
import FormData from 'form-data';

export const config = {
  runtime: 'nodejs',
};

export async function POST(req) {
  const formData = await req.formData();
  const jdFile = formData.get('jd');
  const resumeFiles = formData.getAll('resumes');
  const userName = formData.get('name') || 'User';
  const userEmail = formData.get('email') || '';

  if (!jdFile || resumeFiles.length === 0) {
    console.error('[ERROR] Missing JD or resumes');
    return NextResponse.json({ error: 'Missing JD or resumes' }, { status: 400 });
  }

  const jdId = uuid();
  const jdName = jdFile.name;
  const jdPath = path.join(os.tmpdir(), `${jdId}-${jdName}`);
  await fs.writeFile(jdPath, Buffer.from(await jdFile.arrayBuffer()));
  // console.log('[INFO] JD saved to:', jdPath);

  const resumeMap = new Map();
  for (const resumeFile of resumeFiles) {
    const resumeId = uuid();
    const resumeName = resumeFile.name;
    const resumePath = path.join(os.tmpdir(), `${resumeId}-${resumeName}`);
    await fs.writeFile(resumePath, Buffer.from(await resumeFile.arrayBuffer()));
    resumeMap.set(resumeName, resumePath);
  }
  // console.log('[INFO] Resumes saved:', [...resumeMap.entries()]);

  // === Call FastAPI ===
  let llmResults;
  try {
    const form = new FormData();
    form.append('jd', Buffer.from(await jdFile.arrayBuffer()), jdFile.name);
    for (const file of resumeFiles) {
      form.append('resumes', Buffer.from(await file.arrayBuffer()), file.name);
    }

    const fastapiResponse = await axios.post(
      'http://localhost:8000/run-pipeline',
      form,
      { headers: form.getHeaders() }
    );

    if (fastapiResponse.status !== 200) {
      throw new Error('LLM pipeline failed.');
    }

    llmResults = fastapiResponse.data.results;
    console.log('[INFO] LLM results received:', llmResults);
  } catch (err) {
    console.error('[ERROR] FastAPI call failed:', err.message);
    return NextResponse.json({ error: 'LLM analysis failed' }, { status: 500 });
  }

  const results = [];

  const normalize = (val) => {
    if (Array.isArray(val)) return val.join('; ');
    if (val === null || val === undefined) return null;
    return String(val);
  };

  const getSafe = (obj, key) => {
    if (!obj || typeof obj !== 'object') return null;
    const found = Object.keys(obj).find(k => k.toLowerCase() === key.toLowerCase());
    return found ? obj[found] : null;
  };

  for (const item of llmResults) {
    const resumeKey = Object.keys(item)[0];
    const data = item[resumeKey];

    const matchedEntry = Array.from(resumeMap.entries()).find(([name]) =>
      resumeKey.toLowerCase().includes(name.toLowerCase().split('.')[0])
    );
    const actualResumeName = matchedEntry ? matchedEntry[0] : resumeKey.split('_vs_')[0];

    try {
      const newResult = await prisma.resumeAnalysis.create({
        data: {
          resumeName: actualResumeName,
          jdName,
          overallScore: data?.OverallMatchPercentage ?? null,
          shortlisted: (data?.OverallMatchPercentage ?? 0) > 50,
          overallExplanation: data?.why_overall_match_is_this ?? null,
          aiEstimate:
            data?.AI_Generated_Estimate_Percentage ??
            data?.Ai_Generated_Estimate_Percentage ??
            getSafe(data, 'AI_Generated_Estimate_Percentage') ??
            null,
          skillsMatch: data?.Skills?.match_pct ?? null,
          skillsReason: data?.Skills?.explanation ?? null,
          skillsResumeValue: normalize(data?.Skills?.resume_value),
          skillsJDValue: normalize(data?.Skills?.job_description_value),
          educationMatch: data?.Education?.match_pct ?? null,
          educationReason: data?.Education?.explanation ?? null,
          educationResumeValue: normalize(data?.Education?.resume_value),
          educationJDValue: normalize(data?.Education?.job_description_value),
          jobRoleMatch: data?.['Job Role']?.match_pct ?? null,
          jobRoleReason: data?.['Job Role']?.explanation ?? null,
          jobRoleResumeValue: normalize(data?.['Job Role']?.resume_value),
          jobRoleJDValue: normalize(data?.['Job Role']?.job_description_value),
          experienceMatch: data?.Experience?.match_pct ?? null,
          experienceReason: data?.Experience?.explanation ?? null,
          experienceResumeValue: normalize(data?.Experience?.resume_value),
          experienceJDValue: normalize(data?.Experience?.job_description_value),
        },
      });

      newResult.userName = userName;
      newResult.userEmail = userEmail;
      results.push(newResult);
    } catch (err) {
      console.error(`[ERROR] Failed to save analysis for ${actualResumeName}:`, err.message);
    } finally {
      const pathToDelete = resumeMap.get(actualResumeName);
      if (pathToDelete) {
        await fs.unlink(pathToDelete).catch(() => {});
      }
    }
  }

  if (userEmail) {
    try {
      await sendEmail(userEmail, userName, results);
    } catch (err) {
      console.error('[ERROR] Failed to send email:', err.message);
    }
  }

  await fs.unlink(jdPath).catch(() => {});
  return NextResponse.json({ results }, { status: 200 });
}