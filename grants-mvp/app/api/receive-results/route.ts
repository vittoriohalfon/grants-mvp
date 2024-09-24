import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

interface Result {
  prompt: string;
  answer: string;
}

interface RequestBody {
  domain: string;
  results: Result[];
}

export async function POST(req: Request) {
  try {
    // Add CORS headers
    const headers = new Headers({
      'Access-Control-Allow-Origin': '*', // Be more specific in production
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, x-request-id',
    });

    // Handle preflight request
    if (req.method === 'OPTIONS') {
      return new NextResponse(null, { headers });
    }

    const body: RequestBody = await req.json();
    const requestId = req.headers.get('x-request-id');

    console.log('Received request with headers:', req.headers);
    console.log('Request ID:', requestId);
    console.log('Received body:', JSON.stringify(body, null, 2));

    if (!requestId) {
      throw new Error('Missing x-request-id header');
    }

    // Validate the presence of expected fields
    if (!body.results || !Array.isArray(body.results) || body.results.length === 0) {
      throw new Error('Missing or invalid results field');
    }

    if (!body.domain || typeof body.domain !== 'string') {
      throw new Error('Missing or invalid domain field');
    }

    // Validate the structure of each result in the results array
    body.results.forEach((result: Result, index: number) => {
      if (!result.prompt || typeof result.prompt !== 'string') {
        throw new Error(`Missing or invalid prompt in result at index ${index}`);
      }
      if (!result.answer || typeof result.answer !== 'string') {
        throw new Error(`Missing or invalid answer in result at index ${index}`);
      }
    });

    // Store the entire JSON object in Redis
    await redis.set(`result:${requestId}`, JSON.stringify(body), { ex: 3600 }); // Expire after 1 hour

    console.log('Data stored in Redis with key:', `result:${requestId}`);

    return NextResponse.json(
      { message: 'Results received and stored successfully' },
      { headers }
    );

  } catch (error) {
    console.error('Error receiving results:', error);
    return NextResponse.json(
      { error: 'Failed to receive results', details: error instanceof Error ? error.message : 'An unknown error occurred' },
      { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } }
    );
  }
}