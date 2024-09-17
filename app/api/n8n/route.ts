import { NextResponse } from 'next/server';

const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || 'http://localhost:5678/webhook/analyse-domain';

export async function POST(req: Request) {
  try {
    const { domain } = await req.json();

    // Send data to n8n
    const n8nResponse = await fetch(N8N_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ domain }),
    });

    if (!n8nResponse.ok) {
      throw new Error('Failed to send data to n8n');
    }

    return NextResponse.json({ message: 'Data sent to n8n successfully' });
  } catch (error) {
    console.error('Error sending data to n8n:', error);
    return NextResponse.json({ error: 'Failed to send data to n8n' }, { status: 500 });
  }
}