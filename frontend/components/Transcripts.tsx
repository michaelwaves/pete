'use client';

import React from 'react';

type TranscriptItem = {
    speaker: string;
    text: string;
};

type Props = {
    transcript: TranscriptItem[];
};

export default function Transcript({ transcript }: Props) {
    return (
        <div className="max-w-2xl mx-auto p-6 space-y-4">
            {transcript.map((entry, index) => (
                <div key={index} className="text-lg leading-relaxed">
                    <span className="font-semibold text-green-600">{entry.speaker}:</span>{' '}
                    <span>{entry.text}</span>
                </div>
            ))}
        </div>
    );
}
