import { GoogleGenAI, Type } from "@google/genai";
import { NextRequest, NextResponse } from "next/server";

const GEMINI_API_KEY = process.env.GEMINI_API_KEY!
const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

export async function POST(req: NextRequest) {
    const data = await req.json();
    const text = data.text;

    const config = {
        responseMimeType: 'application/json',
        responseSchema: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    speaker: {
                        type: Type.STRING,
                        description: 'Name or role of the speaker',
                        nullable: false,
                    },
                    text: {
                        type: Type.STRING,
                        description: 'Text spoken by the speaker',
                        nullable: false,
                    },
                },
                required: ['speaker', 'text'],
            },
        },
    }


    const prompt = `
    Based on the provided text :${text}, format it into a short podcast, 5-10 minutes long, with punctuation based on the following
    Sentence	Notes
what do you mean.	a simple period at the end of the sentence renders it a non-question
what do you mean?	a simple question mark indicates an unmarked question
what do you mean?!	adding an exclamation point makes the question more excited
what do you mean!?	changing the order of the exclamation point and question mark makes a different sort of question
what do you mean??	multiple question marks can also change the type of question prosody
i i think it’s pretty cool	putting a word twice in a row can create more realistic, flawed human speech
i- i think it’s pretty cool	adding a dash immediately after some words can give a cut-off, false start sort of realism
Sentence	Notes
so it’s kind of funny.	without any comma, there will be no pause
so, it’s kind of funny.	adding a comma creates a slight pause
so. it’s kind of funny.	adding a period creates a longer pause

format it in json as  

{
speaker : one of "abbie",
			"allison",
			"ally",
			"alona",
			"amber",
			"ana",
			"antoine",
			"armon",
			"brenda",
			"brittany",
			"carol",
			"colin",
			"courtney",
			"elena",
			"elliot",
text: "string"
}
    `
    const response = await ai.models.generateContent({
        model: 'gemini-2.0-flash',
        contents: prompt,
        config: config
    })

    console.log(response.text)

    const script = await response.text

    return NextResponse.json({
        script
    })

}