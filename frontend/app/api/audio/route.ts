import { NextResponse } from 'next/server';

const RIME_API_KEY = process.env.RIME_API_KEY

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { speaker, text } = body;

        if (!speaker || !text) {
            return NextResponse.json({ error: 'Missing speaker or text' }, { status: 400 });
        }

        const rimeResponse = await fetch('https://users.rime.ai/v1/rime-tts', {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                Authorization: `Bearer ${RIME_API_KEY}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                speaker,
                text,
                lang: 'eng',
                audioFormat: 'mp3',
                samplingRate: 22050,
                speedAlpha: 1.0,
                reduceLatency: false,
            }),
        });

        const data = await rimeResponse.json();

        return NextResponse.json(data, { status: rimeResponse.status });
    } catch (err) {
        console.error(err);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
