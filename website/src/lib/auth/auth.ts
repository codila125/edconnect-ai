// This file is where the authentication configuration is set up using Better Auth.
// It includes the database adapter, social providers, and database schema.
// This can be built with help of Drizzle ORM and Better Auth.
// From here we can build schema for databse using 'npx @better-auth/cli generate' command.

import { betterAuth } from "better-auth";
import { reactStartCookies } from "better-auth/react-start";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import db from "../db/drizzle";
import * as schema from "../db/auth-schema";
import { GOOGLE_CLIENT_ID } from "../env";
import { GOOGLE_CLIENT_SECRET } from "../env";

export const auth = betterAuth({
    user: {
        additionalFields: {
            // additional fields to be added to the user table
            role: {
                type: "string",
                required: false,
                defaultValue: "user",
                input: true, // allow user to set role, else it will be set to default value
            },
        },
    },
    database: drizzleAdapter(db, {
        // use drizzle adapter to connect to the database
        // sqlite is also supported, but we are using PostgreSQL here
        provider: "pg", // specify the database provider, here we are using PostgreSQL
        // you can also use other providers like MySQL, SQLite, etc.
        schema: schema,
        // specify the schema to be used, here we are using the auth-schema defined in auth-schema.ts
    }),
    socialProviders: {
        // configure social providers for authentication
        google: {
            clientId: GOOGLE_CLIENT_ID as string,
            clientSecret: GOOGLE_CLIENT_SECRET as string,
        },
    },
    // you can add more social providers like Facebook, Twitter, etc. here
    // can also use email and password authentication
    plugins: [reactStartCookies()],
});
