import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import FacebookProvider from "next-auth/providers/facebook";
import GitHubProvider from "next-auth/providers/github";
import CredentialsProvider from "next-auth/providers/credentials";

import { findUserByEmailOrPhone } from "@/lib/users"; 
import { verifyOAuthLogin } from "@/lib/oauthSecurity"; // NEW IMPORT

const handler = NextAuth({
    providers: [
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID || "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
        }),
        FacebookProvider({
            clientId: process.env.FACEBOOK_CLIENT_ID || "",
            clientSecret: process.env.FACEBOOK_CLIENT_SECRET || "",
        }),
        GitHubProvider({
            clientId: process.env.GITHUB_CLIENT_ID || "",
            clientSecret: process.env.GITHUB_CLIENT_SECRET || "",
        }),
        CredentialsProvider({
            name: "Credentials",
            credentials: {
                identifier: { label: "Email or Phone", type: "text" },
                password: { label: "Password", type: "password" },
            },
            async authorize(credentials) {
                try {
                    const res = await fetch(
                        `${process.env.NEXTAUTH_URL || "http://localhost:3000"}/api/login`,
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                identifier: credentials.identifier,
                                password: credentials.password,
                            }),
                        }
                    );
                    const data = await res.json();
                    if (data.success && data.user) {
                        return {
                            id: data.user.id,
                            name: data.user.name,
                            email: data.user.email,
                            riskScore: data.riskScore,
                            riskLevel: data.riskLevel,
                        };
                    }
                    return null;
                } catch (error) {
                    return null;
                }
            },
        }),
    ],
    session: {
        strategy: "jwt",
    },
    callbacks: {
        async signIn({ user, account }) {
            // Let standard credentials through
            if (account.provider === "credentials") return true;

            // For Google/GitHub, run the native security function directly!
            if (["google", "github"].includes(account.provider)) {
                try {
                    // Look how much cleaner and faster this is!
                    const securityCheck = await verifyOAuthLogin(user.email);

                    if (securityCheck.exists && securityCheck.allowed) {
                        return true; // Let them in!
                    }
                    
                    // Optional: You can redirect to an error page if they fail the check
                    // return "/login?error=AccessDenied"; 
                    return false; 

                } catch (error) {
                    console.error("OAuth Security Check Failed:", error);
                    return false; 
                }
            }
            return false;
        },

        async jwt({ token, user, account }) {
            if (user) {
                token.id = user.id;

                if (account && account.provider !== "credentials") {
                    const dbUser = findUserByEmailOrPhone(user.email);
                    if (dbUser) {
                        token.id = dbUser.id; 
                        token.riskScore = dbUser.riskScore; 
                        token.riskLevel = dbUser.riskLevel;
                    }
                } else {
                    token.riskScore = user.riskScore;
                    token.riskLevel = user.riskLevel;
                }
            }

            if (account) {
                token.authProvider = account.provider;
                token.oauthTokenCaptured = Boolean(account.access_token || account.id_token);
                token.oauthTokenType = account.token_type || null;
                token.oauthScope = account.scope || null;
            }
            return token;
        },

        async session({ session, token }) {
            session.user.id = token.id;
            session.user.riskScore = token.riskScore;
            session.user.riskLevel = token.riskLevel;
            session.user.authProvider = token.authProvider || null;
            session.user.oauthTokenCaptured = Boolean(token.oauthTokenCaptured);
            session.user.oauthTokenType = token.oauthTokenType || null;
            session.user.oauthScope = token.oauthScope || null;
            return session;
        },
    },
    pages: {
        signIn: "/",
    },
    secret: process.env.NEXTAUTH_SECRET || "ares-auth-secret-key-2025",
});

export { handler as GET, handler as POST };