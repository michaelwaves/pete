import pg from "pg-promise";

const DATABASE_URL = process.env.DATABASE_URL

if (!DATABASE_URL) {
    throw new Error("Please set environment DATABASE_URL")
}

const globalDb = global as typeof global & { helpers?: pg.IHelpers, db?: pg.IDatabase<object> }

if (!globalDb.db) {
    const pgp = pg();
    const helpers = pgp.helpers;
    globalDb.db = pgp(DATABASE_URL)
    globalDb.helpers = helpers
}

export const db = globalDb.db;
export const helpers = globalDb.helpers;