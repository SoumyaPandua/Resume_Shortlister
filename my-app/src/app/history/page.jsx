'use client';

import { useEffect, useState } from 'react';
import { Button } from "@/components/ui/button";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
} from "@/components/ui/pagination";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import ResultModal from '@/components/ResultModal';
import axios from 'axios';

export default function HistoryPage() {
  const [data, setData] = useState([]);
  const [selected, setSelected] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [jobRole, setJobRole] = useState('all');
  const [jdName, setJdName] = useState('all');
  const [meta, setMeta] = useState({ jobRoles: [], jdNames: [] });

  const fetchData = async (page = 1) => {
    try {
      const res = await axios.get('/api/history', {
        params: {
          page,
          limit: 8,
          jobRole,
          jdName,
        },
      });
      setData(res.data.data);
      setPage(res.data.page);
      setTotalPages(res.data.totalPages);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const fetchMeta = async () => {
    try {
      const res = await axios.get('/api/history/meta');
      setMeta(res.data);
    } catch (err) {
      console.error('Failed to fetch meta:', err);
    }
  };

  useEffect(() => {
    fetchMeta();
  }, []);

  useEffect(() => {
    fetchData(page);
  }, [page, jobRole, jdName]);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Resume Analysis History</h1>

      <div className="flex flex-wrap gap-4 items-center">
        <Select value={jobRole} onValueChange={setJobRole}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select Job Role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            {meta.jobRoles.map((role, idx) => (
              <SelectItem key={idx} value={role}>{role}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={jdName} onValueChange={setJdName}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select JD" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All JDs</SelectItem>
            {meta.jdNames.map((jd, idx) => (
              <SelectItem key={idx} value={jd}>{jd}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full text-sm border-collapse">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2 border">Resume</th>
              <th className="p-2 border">JD</th>
              <th className="p-2 border">Skill</th>
              <th className="p-2 border">Job Role</th>
              <th className="p-2 border">Edu</th>
              <th className="p-2 border">Exp</th>
              <th className="p-2 border">Overall</th>
              <th className="p-2 border">AI</th>
              <th className="p-2 border">Shortlisted</th>
              <th className="p-2 border">Date</th>
              <th className="p-2 border">View</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, idx) => (
              <tr key={idx} className="border-t text-center">
                <td className="p-2">{item.resumeName}</td>
                <td className="p-2">{item.jdName}</td>
                <td className="p-2">{item.skillsMatch}%</td>
                <td className="p-2">{item.jobRoleMatch}%</td>
                <td className="p-2">{item.educationMatch}%</td>
                <td className="p-2">{item.experienceMatch}%</td>
                <td className="p-2">{item.overallScore}%</td>
                <td className="p-2">{item.aiEstimate}%</td>
                <td className="p-2">{item.shortlisted ? 'Yes' : 'No'}</td>
                <td className="p-2">{new Date(item.scannedAt).toLocaleDateString()}</td>
                <td className="p-2">
                  <Button variant="link" onClick={() => setSelected(item)}>
                    View
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              onClick={() => setPage(p => Math.max(1, p - 1))}
              className={page === 1 ? 'opacity-50 pointer-events-none' : ''}
            />
          </PaginationItem>
          <PaginationItem>
            <span className="px-4 py-1">Page {page} of {totalPages}</span>
          </PaginationItem>
          <PaginationItem>
            <PaginationNext
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              className={page === totalPages ? 'opacity-50 pointer-events-none' : ''}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>

      {selected && (
        <ResultModal result={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}