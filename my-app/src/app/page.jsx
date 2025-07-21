'use client';

import { useState, useEffect } from 'react';
import ResumeUploader from '@/components/ResumeUploader';
import JDUploader from '@/components/JDUploader';
import UploadProgress from '@/components/UploadProgress';
import ResultsSummary from '@/components/ResultsSummary';
import ResultTable from '@/components/ResultTable';
import toast from 'react-hot-toast';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function Home() {
  const [resumes, setResumes] = useState([]);
  const [jd, setJd] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleAnalyze = async () => {
    if (!resumes.length || !jd) {
      toast.error('Please upload resumes and a job description!');
      return;
    }

    if (!name || !email) {
      toast.error('Please enter your name and email!');
      return;
    }

    const formData = new FormData();
    resumes.forEach(file => formData.append('resumes', file));
    formData.append('jd', jd);
    formData.append('name', name);
    formData.append('email', email);

    try {
      setLoading(true);
      setUploadProgress(0);

      // Simulate progress manually
      let fakeProgress = 0;
      const interval = setInterval(() => {
        fakeProgress += 10;
        setUploadProgress(fakeProgress);
        if (fakeProgress >= 90) clearInterval(interval);
      }, 100);

      const response = await axios.post('/api/analyze', formData);

      clearInterval(interval);
      setUploadProgress(100);

      const { results } = response.data;
      setAnalysisResults(results);
      toast.success('Analysis completed!');
    } catch (err) {
      console.error(err);
      toast.error('Error analyzing resumes!');
    } finally {
      setLoading(false);
      setTimeout(() => setUploadProgress(0), 1000);
      setResumes([]); // Reset resume uploader
      setJd(null);     // Reset JD uploader
    }
  };

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Resume Shortlister</h1>

      <div className="grid md:grid-cols-2 gap-4">
        <ResumeUploader setFiles={setResumes} />
        <JDUploader setFile={setJd} />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Your Name</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            data-lpignore="true"
            data-form-type="other"
            autoComplete="off"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Your Email</Label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            data-lpignore="true"
            data-form-type="other"
            autoComplete="off"
            data-temp-mail-org="disabled"
            data-1p-ignore
            data-lastpass-ignore
          />
        </div>
      </div>

      <UploadProgress progress={uploadProgress} />

      <Button
        onClick={handleAnalyze}
        disabled={loading}
      >
        {loading ? 'Waiting for response...' : 'Analyze Resumes'}
      </Button>

      {analysisResults.length > 0 && (
        <>
          <ResultsSummary results={analysisResults} />
          <ResultTable results={analysisResults} />
          <div className="mt-4 text-right">
            <Button asChild variant="link">
              <Link href="/history">View History</Link>
            </Button>
          </div>
        </>
      )}
    </main>
  );
}