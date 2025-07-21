import { prisma } from '@/db';
import { NextResponse } from 'next/server';

export async function GET(req) {
  try {
    const { searchParams } = new URL(req.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    const jobRole = searchParams.get('jobRole');
    const jdName = searchParams.get('jdName');

    const where = {};

    if (jobRole && jobRole !== 'all') {
      where.jobRoleJDValue = jobRole;
    }
    if (jdName && jdName !== 'all') {
      where.jdName = jdName;
    }

    const [resumes, total] = await Promise.all([
      prisma.resumeAnalysis.findMany({
        where,
        skip: (page - 1) * limit,
        take: limit,
        orderBy: { scannedAt: 'desc' },
      }),
      prisma.resumeAnalysis.count({ where }),
    ]);

    return NextResponse.json({
      data: resumes,
      total,
      page,
      totalPages: Math.ceil(total / limit),
    });
  } catch (error) {
    console.error("❌ Error in /api/history:", error);
    return NextResponse.json({ error: 'Failed to fetch history' }, { status: 500 });
  }
}