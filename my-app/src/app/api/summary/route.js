import { prisma } from "@/db";
import { NextResponse } from "next/server";

export async function GET() {
  const summaries = await prisma.resumeAnalysis.groupBy({
    by: ["jobRoleResumeValue"],
    _count: { jobRoleResumeValue: true },
    _avg: { overallScore: true },
    where: {},
  });

  const shortlistedCounts = await prisma.resumeAnalysis.findMany({
    select: { jobRoleResumeValue: true, shortlisted: true },
  });

  const summaryWithShortlisted = summaries.map((s) => {
    const shortlisted = shortlistedCounts.filter(
      (r) => r.jobRoleResumeValue === s.jobRoleResumeValue && r.shortlisted
    ).length;

    return {
      jobRoleResumeValue: s.jobRoleResumeValue,
      total: s._count.jobRoleResumeValue,
      shortlisted,
      averageScore: Number(s._avg.overallScore?.toFixed(1)),
    };
  });

  return NextResponse.json({ summary: summaryWithShortlisted });
}