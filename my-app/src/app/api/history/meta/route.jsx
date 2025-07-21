import { prisma } from '@/db';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const [jdNames, jobRoles] = await Promise.all([
      prisma.resumeAnalysis.findMany({
        distinct: ['jdName'],
        select: { jdName: true }
      }),
      prisma.resumeAnalysis.findMany({
        distinct: ['jobRoleJDValue'],
        select: { jobRoleJDValue: true }
      })
    ]);

    return NextResponse.json({
      jdNames: jdNames.map(j => j.jdName).filter(Boolean),
      jobRoles: jobRoles.map(j => j.jobRoleJDValue).filter(Boolean),
    });
  } catch (error) {
    console.error("Failed to fetch meta filters:", error);
    return NextResponse.json({ error: 'Failed to load filters' }, { status: 500 });
  }
}
