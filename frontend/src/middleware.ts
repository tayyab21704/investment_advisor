import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function middleware(req: NextRequest) {
  try {
    // Attempt to extract the JWT session securely. 
    // If decryption fails (e.g. secret changed), it throws an error we can catch.
    const token = await getToken({ 
        req, 
        secret: process.env.NEXTAUTH_SECRET || "super_secret_fallback_key_12345"
    });

    // If no valid decoded token exists, redirect to login
    if (!token) {
      return NextResponse.redirect(new URL('/login', req.url));
    }
    
    // User is authenticated, allow request to proceed natively
    return NextResponse.next();
  } catch (error) {
    // Graceful fallback: If JWT decryption crashes (e.g., old corrupted cookie),
    // force redirect to login instead of crashing the Next.js server with 500.
    console.warn("Middleware JWT Error:", error);
    const response = NextResponse.redirect(new URL('/login', req.url));
    // Clear the corrupted NextAuth cookies to fix the loop
    response.cookies.delete('next-auth.session-token');
    response.cookies.delete('__Secure-next-auth.session-token');
    return response;
  }
}

export const config = {
  matcher: [
    "/((?!api/auth|login|register|_next/static|_next/image|favicon.ico).*)",
  ],
};
