import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';

let redis: Redis;

try {
  redis = new Redis({
    url: process.env.UPSTASH_REDIS_REST_URL,
    token: process.env.UPSTASH_REDIS_REST_TOKEN,
  });
} catch (error) {
  console.error('Failed to initialize Redis:', error);
}

export async function GET(req: Request) {
    if (!redis) {
        return NextResponse.json({ error: 'Redis not initialized' }, { status: 500 });
    }
    
    const { searchParams } = new URL(req.url);
    const requestId = searchParams.get('requestId');

    if (!requestId) {
        return NextResponse.json({ error: 'Missing requestId parameter' }, { status: 400 });
    }

    try {
        const result = await redis.get(`result:${requestId}`);

        if (result) {
            // Parse the result only if it's a string
            const parsedResult = typeof result === 'string' ? JSON.parse(result) : result;
            
            // Validate the structure of the retrieved data
            if (!parsedResult.results || !Array.isArray(parsedResult.results) || !parsedResult.domain) {
                throw new Error('Invalid data structure in stored results');
            }

            return NextResponse.json(parsedResult);
        } else {
            return NextResponse.json({ message: 'Results not found' }, { status: 404 });
        }
    } catch (error) {
        console.error('Error fetching or parsing results:', error);
        return NextResponse.json({ error: 'Failed to fetch or parse results', details: error instanceof Error ? error.message : 'An unknown error occurred' }, { status: 500 });
    }
}