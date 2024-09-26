/*
This endpoint associates a temporary profile with a user's account.
It retrieves the temporary profile data using a tempId, stores it with the user's ID,
and then deletes the temporary profile.
*/ 

import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { auth } from '@clerk/nextjs/server';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

export async function POST(request: Request) {
  try {
    const { userId } = auth();
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Parse the request body, retrieve the tempId
    let tempId;
    try {
        ({ tempId } = await request.json());
    } catch (error) {
        console.error('parsing request body:', error);
        return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
    }


    // Retrieve the temporary profile data
    let tempProfile;
    try {
        tempProfile = await redis.get(`temp_profile:${tempId}`);
    } catch (error) {
        console.error('Error retrieving temporary profile:', error);
        return NextResponse.json({ error: 'Failed to retrieve temporary profile' }, { status: 500 });
    }

    if (!tempProfile) {
      return NextResponse.json({ error: 'Temporary profile not found' }, { status: 404 });
    }

    // Store the profile data associated with the user ID, and delete the temporary profile
    try {
        await redis.set(`user_profile:${userId}`, tempProfile);
        await redis.del(`temp_profile:${tempId}`);
    } catch (error) {
        console.error('Error updating Redis:', error);
        return NextResponse.json({ error: 'Failed to update profile' }, { status: 500 });
    }

    return NextResponse.json({ message: 'Profile associated successfully' });
} catch (error) {
    console.error('Error associating profile:', error);
    return NextResponse.json({ error: 'Failed to associate profile' }, { status: 500 });
  }
}