import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // Here you would typically save the data to your database
    // For now, we'll just log it
    console.log('Confirmed profile data:', data);

    return NextResponse.json({ message: 'Profile confirmed successfully' });
  } catch (error) {
    console.error('Error confirming profile:', error);
    return NextResponse.json({ error: 'Failed to confirm profile' }, { status: 500 });
  }
}