import { NextResponse } from 'next/server';

// Use the same storage mechanism as in receive-results
const results = new Map();

export async function GET(
  req: Request,
  { params }: { params: { requestId: string } }
) {
  const requestId = params.requestId;

  if (results.has(requestId)) {
    return NextResponse.json(results.get(requestId));
  } else {
    return NextResponse.json({ message: 'Results not found' }, { status: 404 });
  }
}