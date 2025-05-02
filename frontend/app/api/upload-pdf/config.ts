import { Type } from "@google/genai";

export const config = {
    responseMimeType: 'application/json',
    responseSchema: {
        type: Type.OBJECT,
        properties: {
            language: {
                type: Type.STRING,
                description: 'Language of the lesson',
                nullable: false,
            },
            units: {
                type: Type.ARRAY,
                items: {
                    type: Type.OBJECT,
                    properties: {
                        markdown: {
                            type: Type.STRING,
                            description: 'Markdown content for the unit',
                            nullable: false,
                        },
                        quiz: {
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    question: {
                                        type: Type.STRING,
                                        description: 'Quiz question text',
                                        nullable: false,
                                    },
                                    answers: {
                                        type: Type.ARRAY,
                                        items: {
                                            type: Type.OBJECT,
                                            properties: {
                                                answer: {
                                                    type: Type.STRING,
                                                    nullable: false,
                                                },
                                                is_correct: {
                                                    type: Type.BOOLEAN,
                                                    nullable: false,
                                                },
                                            },
                                            required: ['answer', 'is_correct'],
                                        },
                                    },
                                },
                                required: ['question', 'answers'],
                            },
                        },
                    },
                    required: ['markdown', 'quiz'],
                },
            },
        },
        required: ['language', 'units'],
    },
};