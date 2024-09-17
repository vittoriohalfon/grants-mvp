// app/api/receive-results/route.ts

import { NextResponse } from 'next/server';

// Use a database in production
const results = new Map();

export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    // Extract the requestId from the request (you might need to add this to your n8n workflow)
    const requestId = req.headers.get('x-request-id') || 'default';

    // Assuming the n8n response is always an array with one object
    const data = body[0].output;

    // Store the results
    results.set(requestId, data);

    return NextResponse.json({ message: 'Results received and stored successfully' });

  } catch (error) {
    console.error('Error receiving n8n results:', error);
    return NextResponse.json({ error: 'Failed to receive n8n results' }, { status: 500 });
  }
}