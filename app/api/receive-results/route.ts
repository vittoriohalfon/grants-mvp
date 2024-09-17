import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

export async function POST(req: Request) {
  try {
    const apiKey = req.headers.get('x-api-key');
    if (apiKey !== process.env.N8N_API_KEY) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await req.json();
    const requestId = req.headers.get('x-request-id');

    console.log('Received request with headers:', req.headers);
    console.log('Request ID:', requestId);
    console.log('Received body from n8n:', JSON.stringify(body, null, 2));

    if (!requestId) {
      throw new Error('Missing x-request-id header');
    }

    await redis.set(`result:${requestId}`, JSON.stringify(body), { ex: 3600 }); // Expire after 1 hour

    console.log('Data stored in Redis with key:', `result:${requestId}`);

    return NextResponse.json({ message: 'Results received and stored successfully' });

  } catch (error) {
    console.error('Error receiving n8n results:', error);
    return NextResponse.json({ error: 'Failed to receive n8n results', details: error instanceof Error ? error.message : 'An unknown error occurred' }, { status: 500 });
  }
}