import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import FacebookProvider from "next-auth/providers/facebook";
import CredentialsProvider from "next-auth/providers/credentials";

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
        async jwt({ token, user }) {
            if (user) {
                token.id = user.id;
                token.riskScore = user.riskScore;
                token.riskLevel = user.riskLevel;
            }
            return token;
        },
        async session({ session, token }) {
            session.user.id = token.id;
            session.user.riskScore = token.riskScore;
            session.user.riskLevel = token.riskLevel;
            return session;
        },
    },
    pages: {
        signIn: "/",
    },
    secret: process.env.NEXTAUTH_SECRET || "ares-auth-secret-key-2025",
});

export { handler as GET, handler as POST };
