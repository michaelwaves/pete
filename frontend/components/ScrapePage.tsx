'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

export default function ScrapePage() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any[] | null>(null);
    const [scripts, setScripts] = useState<any[] | null>(null);

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
            const script = await getScript(json.blogContents[0].text)
            console.log(script.script)
            const frenchScript = await translateScript(script[0].text, 'fr');
            console.log(frenchScript)
            setResult(json);
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


    return (
        <div className="max-w-3xl mx-auto p-6 space-y-6">
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

            {result && (
                <div className="space-y-4">
                    {result.blogContents.map((item, idx) => (
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
