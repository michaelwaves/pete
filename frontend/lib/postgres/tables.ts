"use server"
import { db } from "./db"

interface SessionData {
    chat_history: string[],
    sources: any[][],
}

const createChat = async (data: SessionData) => {
    return db.one(
        `INSERT INTO chats (session_data) 
         VALUES ($1) RETURNING id`,
        [data]
    );
};

const updateChat = async (id: string, data: SessionData) => {
    return db.one(
        `UPDATE chats 
         SET session_data = $1
         WHERE id = $2
         RETURNING id`,
        [data, id]
    );
};

const updateChatTokens = async (id: string, addTokens: number) => {
    console.log("updated tokens")
    const tokenResult = await db.tx(async (t) => {
        // Check if chat exists
        const chat = await t.oneOrNone(`SELECT total_tokens FROM chats WHERE id = $1`, [id]);
        console.log(chat)
        if (chat) {
            // Chat exists, increment total_tokens
            console.log(chat)
            console.log(id)
            return await t.one(
                `UPDATE chats 
                 SET total_tokens = COALESCE(total_tokens,0) + $1 
                 WHERE id = $2 
                 RETURNING id, total_tokens`,
                [addTokens, id]
            );
        } else {
            // Chat does not exist, create new chat with initial tokens
            return await t.one(
                `INSERT INTO chats (id, session_data, total_tokens) 
                 VALUES ($1, $2, $3) RETURNING id, total_tokens`,
                [id, {}, addTokens] // Assuming empty session_data initially
            );
        }
    });
    return tokenResult
};
export { createChat, updateChat, updateChatTokens }