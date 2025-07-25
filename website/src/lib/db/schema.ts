// This file defines the database schema for user authentication using Drizzle ORM with PostgreSQL.
// It is auto generated and should not be manually edited.
// Ensure that the `drizzle.config.ts` file is properly configured to point to this schema file.
// You can also use npx @better-auth/cli generate' to generate this file automatically.
// After this is generated, push it into the database using the `drizzle-kit push` command.
// The schema defined here will be created in database you have configured in drizzle.ts

import { pgTable, text, timestamp, boolean } from "drizzle-orm/pg-core";

export const user = pgTable("user", {
    id: text("id").primaryKey(),
    name: text("name").notNull(),
    email: text("email").notNull().unique(),
    emailVerified: boolean("email_verified")
        .$defaultFn(() => false)
        .notNull(),
    image: text("image"),
    createdAt: timestamp("created_at")
        .$defaultFn(() => /* @__PURE__ */ new Date())
        .notNull(),
    updatedAt: timestamp("updated_at")
        .$defaultFn(() => /* @__PURE__ */ new Date())
        .notNull(),
    role: text("role").default("user"),
});

export const session = pgTable("session", {
    id: text("id").primaryKey(),
    expiresAt: timestamp("expires_at").notNull(),
    token: text("token").notNull().unique(),
    createdAt: timestamp("created_at").notNull(),
    updatedAt: timestamp("updated_at").notNull(),
    ipAddress: text("ip_address"),
    userAgent: text("user_agent"),
    userId: text("user_id")
        .notNull()
        .references(() => user.id, { onDelete: "cascade" }),
});

export const account = pgTable("account", {
    id: text("id").primaryKey(),
    accountId: text("account_id").notNull(),
    providerId: text("provider_id").notNull(),
    userId: text("user_id")
        .notNull()
        .references(() => user.id, { onDelete: "cascade" }),
    accessToken: text("access_token"),
    refreshToken: text("refresh_token"),
    idToken: text("id_token"),
    accessTokenExpiresAt: timestamp("access_token_expires_at"),
    refreshTokenExpiresAt: timestamp("refresh_token_expires_at"),
    scope: text("scope"),
    password: text("password"),
    createdAt: timestamp("created_at").notNull(),
    updatedAt: timestamp("updated_at").notNull(),
});

export const verification = pgTable("verification", {
    id: text("id").primaryKey(),
    identifier: text("identifier").notNull(),
    value: text("value").notNull(),
    expiresAt: timestamp("expires_at").notNull(),
    createdAt: timestamp("created_at").$defaultFn(
        () => /* @__PURE__ */ new Date()
    ),
    updatedAt: timestamp("updated_at").$defaultFn(
        () => /* @__PURE__ */ new Date()
    ),
});

export const classes = pgTable("classes", {
    id: text("id")
        .primaryKey()
        .$defaultFn(() => crypto.randomUUID()),
    className: text("class_name").notNull(),
    classCode: text("class_code")
        .notNull()
        .unique()
        .$defaultFn(() => Math.floor(100000 + Math.random() * 900000).toString()), // 6-digit code
    description: text("description"),
    teacherId: text("teacher_id")
        .notNull()
        .references(() => user.id, { onDelete: "cascade" }),
    createdAt: timestamp("created_at")
        .$defaultFn(() => /* @__PURE__ */ new Date())
        .notNull(),
    activeStart: text("active_start")
        .notNull(),
    activeEnd: text("active_end")
        .notNull(),
});

export const enrollments = pgTable("enrollments", {
    id: text("id")
        .primaryKey()
        .$defaultFn(() => crypto.randomUUID()),
    classId: text("class_id")
        .notNull()
        .references(() => classes.id, { onDelete: "cascade" }),
    studentId: text("student_id")
        .notNull()
        .references(() => user.id, { onDelete: "cascade" }),
});

export const contents = pgTable("contents", {
    id: text("id")
        .primaryKey()
        .$defaultFn(() => crypto.randomUUID()),
    classId: text("class_id")
        .notNull()
        .references(() => classes.id, { onDelete: "cascade" }),
    title: text("title").notNull(),
    body: text("body").notNull(),
    url: text("url"), 
    type: text("type", { enum: ["assignment", "material"] }).notNull(),
    deadline: timestamp("deadline"), // <-- Only set for assignments
    createdAt: timestamp("created_at")
        .$defaultFn(() => /* @__PURE__ */ new Date())
        .notNull(),
});
