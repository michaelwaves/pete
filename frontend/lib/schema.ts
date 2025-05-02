import * as z from 'zod'

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
    language: z.string()
})

export { schema };