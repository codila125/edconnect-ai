// This file contains environment variables and configuration settings
// for the application, such as database connection strings and authentication secrets.
// It is important to keep this file secure and not expose sensitive information.
// Ensure that these variables are set in your environment before running the application.
// Do not commit this file to version control if it contains sensitive information.
// Use a .env file or environment variables to manage these settings securely.
import { env } from "process";

export const DATABASE_URL = env.DATABASE_URL;
export const BETTER_AUTH_SECRET = env.BETTER_AUTH_SECRET;
export const BETTER_AUTH_URL = env.BETTER_AUTH_URL;
export const GOOGLE_CLIENT_ID = env.GOOGLE_CLIENT_ID;
export const GOOGLE_CLIENT_SECRET = env.GOOGLE_CLIENT_SECRET;
