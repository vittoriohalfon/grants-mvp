import { NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';

const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || 'http://localhost:5678/webhook/8756b09a-1e66-4c45-a08d-f11851db23e0';
const CALLBACK_URL = process.env.CALLBACK_URL || 'https://grants-m7dcw60z2-skim-ai.vercel.app/api/receive-results';

export async function POST(req: Request) {
  try {
    const { domain } = await req.json();

    // Generate a unique ID for this request
    const requestId = uuidv4();

    // Send data to n8n
    const n8nResponse = await fetch(N8N_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        domain,
        requestId,
        callbackUrl: CALLBACK_URL,
      }),
    });

    if (!n8nResponse.ok) {
      const errorText = await n8nResponse.text();
      console.error('n8n response error:', errorText);
      throw new Error(`Failed to send data to n8n: ${n8nResponse.status} ${n8nResponse.statusText}`);
    }

    return NextResponse.json({ requestId });

  } catch (error) {
    console.error('Error triggering n8n workflow:', error);
  }
}