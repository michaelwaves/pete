import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY! });

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('pdf') as File;

    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    // Validate file type
    if (file.type !== 'application/pdf') {
      return NextResponse.json(
        { error: 'Only PDF files are allowed' },
        { status: 400 }
      );
    }

    console.log('Received file:', file.name, 'Size:', file.size);

    const arrayBuffer = await file.arrayBuffer();
    const b64Data = Buffer.from(arrayBuffer).toString('base64');

    const contents = [
      {
        text: `Identify all revelant concepts from the following scientific paper pdf. 
        
        For each one, create a lecture of 5-10 units that conforms to the following zod schema. 
        
        const answer = z.object({
            answer: z.string(),
            is_correct: z.boolean(),
        })
        
        const question = z.object({
            question: z.string(),
            answers: z.array(answer)
        })
        
        const unit = z.object({
            markdown: z.string(),
            quiz: z.array(question)
        })
        
        const schema = z.object({
            units: z.array(unit),
            language:z.string()
        })
        
        
        Build up from any basic concepts in math or sciences,
        but make sure the questions and concepts are directly applicable to the paper. If there are any math equations or computer science,
        implement very basic code examples with example numbers in the markdown of each unit
        `,

      },
      {
        inlineData: {
          mimeType: 'application/pdf',
          data: b64Data,
        },
      },
    ]


    const result = await ai.models.generateContent({
      model: 'gemini-2.0-flash',
      contents
    })

    return NextResponse.json({
      message: 'PDF uploaded successfully!',
      filename: file.name,
      size: file.size
    });

  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: 'Failed to upload file' },
      { status: 500 }
    );
  }
}

