import { NextResponse } from 'next/server';
import * as deepl from 'deepl-node';

const authKey = process.env.DEEPL_AUTH_KEY || ''; // Store your API key in an environment variable
const translator = new deepl.Translator(authKey);

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { text, targetLang } = body;

        if (!text) {
            return NextResponse.json({ error: 'Missing text' }, { status: 400 });
        }

        // Default to 'en' if targetLang is not provided
        const language = targetLang || 'en';

        const result = await translator.translateText(text, null, language);
        //@ts-expect-error description: result.text is from deepl docs
        return NextResponse.json({ translatedText: result.text });
    } catch (err) {
        console.error(err);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
