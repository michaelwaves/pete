import { NextRequest, NextResponse } from 'next/server';
import * as cheerio from 'cheerio';


export async function POST(req: NextRequest) {
    const data = await req.json();
    const url = data.url;
    try {
        if (!url || typeof url !== 'string') {
            return NextResponse.json({ error: 'Missing or invalid URL' }, { status: 400 });
        }

        const response = await fetch(url);
        if (!response.ok) {
            return NextResponse.json({ error: 'Failed to fetch URL' }, { status: 400 });
        }

        const html = await response.text();
        const $ = cheerio.load(html);

        const links = $('a[href^="/blog/"].hover\\:text-green-600');

        const blogContents: { link: string; text: string }[] = [];

        for (let i = 0; i < links.length; i++) {
            const el = links[i];
            const href = $(el).attr('href');

            if (href) {
                const blogUrl = `https://quantoflow.com${href}`; // Adjust as needed
                try {
                    const blogRes = await fetch(blogUrl);
                    const blogHtml = await blogRes.text();
                    const $$ = cheerio.load(blogHtml);

                    // Adjust selector to match your actual blog post container
                    const text = $$('article').text().trim();

                    blogContents.push({ link: blogUrl, text });
                } catch (err) {
                    blogContents.push({ link: blogUrl, text: 'Failed to fetch blog content' });
                }
            }
        }

        return NextResponse.json({ blogContents });

    } catch (error) {
        console.log(error)
        return NextResponse.json({ error: 'Unexpected error', detail: (error as Error).message }, { status: 500 });
    }
}
