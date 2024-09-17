import { NextResponse } from 'next/server';

const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || 'http://localhost:5678/webhook/your-webhook-id';

export async function POST(req: Request) {
  try {
    const { domain } = await req.json();

    // Generate a unique ID for this request
    const requestId = crypto.randomUUID();

    // Send data to n8n
    const n8nResponse = await fetch(N8N_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        domain,
        requestId,
        callbackUrl: `http://localhost:3000/api/receive-results`,
      }),
    });

    if (!n8nResponse.ok) {
      throw new Error('Failed to send data to n8n');
    }

    return NextResponse.json({ requestId });

  } catch (error) {
    console.error('Error triggering n8n workflow:', error);
    return NextResponse.json({ error: 'Failed to trigger n8n workflow' }, { status: 500 });
  }
}