// This endpoint temporarily stores a user's profile data before account creation.
// It generates a unique temporary ID, stores the profile data in Redis with a 1-hour expiration,
// and returns the temporary ID to the client.

import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { v4 as uuidv4 } from 'uuid';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // Generate a unique temporary ID
    const tempId = uuidv4();

    // Store the data in Redis with an expiration of 1 hour
    await redis.set(`temp_profile:${tempId}`, JSON.stringify(data), { ex: 3600 });

    return NextResponse.json({ tempId, message: 'Profile data stored temporarily' });
  } catch (error) {
    console.error('Error storing temporary profile:', error);
    return NextResponse.json({ error: 'Failed to store temporary profile' }, { status: 500 });
  }
}