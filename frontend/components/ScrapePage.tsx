'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import Transcript from './Transcripts';

export default function ScrapePage() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any[] | null>(null);

    const [script, setScript] = useState<any>(null);
    const [frenchScript, setFrenchScript] = useState<string | null>(null)

    const [audioUrl, setAudioUrl] = useState<string | null>(null)

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch('/api/scrape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });

            const json = await res.json();
            setResult(json);

            const script = await getScript(json.blogContents[0].text)
            setScript(JSON.parse(script.script))

            const frenchScript = await translateScript(script.script, 'fr');
            setFrenchScript(frenchScript.translatedText)
            console.log(frenchScript.translatedText)


        } catch (err) {
            console.error(err);
            setResult([{ error: 'Failed to fetch data' }]);
        } finally {
            setLoading(false);
        }
    }

    async function getScript(text: string) {
        const res = await fetch('/api/script', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });

        console.log(res)
        return await res.json()
    }

    async function translateScript(text: string, targetLang = 'en') {
        const res = await fetch(`/api/translate`, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, targetLang }),

        })

        console.log(res)
        return await res.json()
    }

    async function getAudio() {
        const text = "hello this is a test"
        const speaker = "brenda"
        const res = await fetch(`/api/audio`, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, speaker }),

        })
        const j = await res.json()
        const base64 = j.audioContent; // should be base64-encoded string
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }

        const blob = new Blob([bytes], { type: 'audio/mp3' }); // or audio/wav depending on API
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
    }


    return (
        <div className="max-w-3xl mx-auto p-6 space-y-6">
            <Button onClick={getAudio}>Get Audio</Button>
            {audioUrl && (
                <audio controls src={audioUrl} className="w-full" />
            )}
            <Card>
                <CardContent className="p-6 space-y-4">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="url">Enter Blog Index URL</Label>
                            <Input
                                id="url"
                                type="url"
                                placeholder="https://example.com/blog"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                required
                            />
                        </div>
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Scraping...' : 'Scrape'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
            {script && <Transcript transcript={script} />}

            {result && (
                <div className="space-y-4">

                    {result.blogContents.map((item: any, idx: any) => (
                        <Card key={idx}>
                            <CardContent className="p-4 space-y-2">
                                <div className="font-semibold text-green-700">Link:</div>
                                <div className="text-sm break-words text-gray-700">{item.link}</div>

                                <div className="font-semibold text-green-700 mt-4">Text:</div>
                                <Textarea
                                    value={item.text}
                                    className="text-sm whitespace-pre-wrap h-48"
                                    readOnly
                                />
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
