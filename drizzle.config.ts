// This file is used to configure Drizzle ORM for this application.
// It sets up the database connection and specifies the schema file for authentication.
// Ensure that the DATABASE_URL environment variable is set before running this configuration.
// This configuration is essential for the application to interact with the PostgreSQL database using Drizzle ORM

import { defineConfig } from "drizzle-kit";
import { DATABASE_URL } from "./src/lib/env";

export default defineConfig({
    out: "./src/lib/db",
    schema: "./src/lib/db/schema.ts", // Path to the schema file for authentication
    dialect: "postgresql",
    dbCredentials: {
        url: DATABASE_URL!,
    },
});
