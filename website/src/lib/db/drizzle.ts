// This file is used to set up the database connection using Drizzle ORM with Neon as the database provider.
// It imports the necessary modules and initializes the database connection using the provided DATABASE_URL.
import { drizzle } from "drizzle-orm/neon-http";
import { neon } from "@neondatabase/serverless";
import { DATABASE_URL } from "../env";

const sql = neon(DATABASE_URL!); //Connects to the Neon database using the provided DATABASE_URL.
// The DATABASE_URL is expected to be set in the environment variables, ensuring secure access to the database.
const db = drizzle(sql); // Initializes the Drizzle ORM with the Neon SQL client, allowing for database operations using Drizzle's API.

export default db; // Exports the initialized database instance for use in other parts of the application, such as authentication and data management.
