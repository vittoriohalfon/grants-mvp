import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { auth } from '@clerk/nextjs/server';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

// This endpoint retrieves a user's profile data.
// It uses the authenticated user's ID to fetch their profile from Redis
// and returns the profile data if found.

export async function GET() {
  try {
    const { userId } = auth();
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const profileData = await redis.get(`user_profile:${userId}`);

    if (!profileData) {
      return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
    }

    // Check if profileData is a string before parsing
    return NextResponse.json(typeof profileData === 'string' ? JSON.parse(profileData) : profileData);
  } catch (error) {
    console.error('Error fetching profile:', error);
    return NextResponse.json({ error: 'Failed to fetch profile' }, { status: 500 });
  }
}