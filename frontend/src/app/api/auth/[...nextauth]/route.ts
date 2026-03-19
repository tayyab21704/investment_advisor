import NextAuth, { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
  secret: process.env.NEXTAUTH_SECRET || "super_secret_fallback_key_12345",
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials, req) {
        if (!credentials?.email || !credentials?.password) return null;
        
        try {
          const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
          const res = await fetch(`${apiBase}/api/auth/login`, {
            method: 'POST',
            body: JSON.stringify({ email: credentials.email, password: credentials.password }),
            headers: { "Content-Type": "application/json" }
          });
          
          if (!res.ok) {
            return null;
          }
          const user = await res.json();
          if (user) {
            return {
              id: user.user_id,
              name: user.name,
              email: user.email,
              token: user.token
            };
          }
        } catch (e) {
          console.error("Auth Exception", e);
        }
        return null;
      }
    })
  ],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.id = user.id;
        if ('token' in user) {
          token.backendToken = user.token;
        }
      }
      return token;
    },
    async session({ session, token }: any) {
      if (session.user && token) {
        session.user.id = token.id as string;
        session.backendToken = token.backendToken as string;
      }
      return session;
    }
  },
  pages: {
    signIn: "/login",
  }
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
