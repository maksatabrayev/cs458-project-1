import { NextResponse } from "next/server";
import { resetUserStatus, getAllUsers, findUserByEmail } from "@/lib/users";

// GET: List all users with their current status
export async function GET() {
    const users = getAllUsers();
    return NextResponse.json({ users });
}

// POST: Reset a user's account to active status
export async function POST(request) {
    try {
        const body = await request.json();
        const { userId, email } = body;

        let user;
        if (userId) {
            user = resetUserStatus(userId);
        } else if (email) {
            const found = findUserByEmail(email);
            if (found) {
                user = resetUserStatus(found.id);
            }
        }

        if (!user) {
            return NextResponse.json({ error: "User not found" }, { status: 404 });
        }

        return NextResponse.json({
            success: true,
            message: `Account reset to active for ${user.name}`,
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                status: user.status,
                failedAttempts: user.failedAttempts,
            },
        });
    } catch (error) {
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
