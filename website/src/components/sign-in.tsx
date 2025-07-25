// This file is used to handle sign-in functionality in a React component.
// It provides buttons for signing in as a teacher or a student using Google authentication.

import { authClient } from "../lib/auth/auth-client";

export default function SignIn() {
    return (
        <div>
            <h1>Sign In</h1>
            <button
                onClick={() =>
                    authClient.signIn.social({
                        provider: "google",
                        errorCallbackURL: "/error",
                        callbackURL: "/api/hello/teacher", //This is the URL where the user will be redirected after a successful sign-in.
                        newUserCallbackURL: "/api/hello/teacher",
                        //When a new user signs in, they will be redirected to this URL if they are a teacher
                        // and their role is set to teacher.
                        //This is handled by the server route at /api/hello/$.
                        //The server route will check if the user already has a role and assign the teacher role
                        //if they don't have one. If they already have a role, it will return an error response.
                        disableRedirect: false,
                    })
                }
            >
                Sign in as Teacher
            </button>
            <button
                onClick={() =>
                    authClient.signIn.social({
                        provider: "google",
                        errorCallbackURL: "/error",
                        callbackURL: "/api/hello/student", //Similar to above but for student role
                        newUserCallbackURL: "/api/hello/student", //Similar to above but for student role
                        disableRedirect: false,
                    })
                }
            >
                Sign in Student
            </button>
        </div>
    );
}
