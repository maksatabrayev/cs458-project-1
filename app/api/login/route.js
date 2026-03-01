import { NextResponse } from "next/server";

const {
    findUserByEmailOrPhone,
    validatePassword,
    recordFailedAttempt,
    recordSuccessfulLogin,
} = require("@/lib/users");
const { calculateRiskScore } = require("@/lib/riskEngine");
const { analyzeFraud } = require("@/lib/llmClient");

export async function POST(request) {
    try {
        const body = await request.json();
        const { identifier, password } = body;

        // Get client IP
        const ip =
            request.headers.get("x-forwarded-for") ||
            request.headers.get("x-real-ip") ||
            "127.0.0.1";
        const userAgent = request.headers.get("user-agent") || "Unknown";

        // Validate input
        if (!identifier || !password) {
            return NextResponse.json(
                { error: "Email/Phone and password are required" },
                { status: 400 }
            );
        }

        // Find user
        const user = findUserByEmailOrPhone(identifier);
        if (!user) {
            return NextResponse.json(
                { error: "Invalid credentials. User not found." },
                { status: 401 }
            );
        }

        // Calculate risk score BEFORE any status checks
        const riskAssessment = calculateRiskScore({
            user,
            ip,
            userAgent,
            timestamp: new Date(),
        });

        // Check if account is suspended
        if (user.status === "suspended") {
            return NextResponse.json(
                {
                    error: "Account is suspended. Contact administrator.",
                    status: user.status,
                    accountStatus: "suspended",
                    riskScore: riskAssessment.score,
                    riskLevel: riskAssessment.level,
                },
                { status: 403 }
            );
        }

        // If risk is high, run LLM fraud analysis
        let llmAnalysis = null;
        if (riskAssessment.requiresLLMAnalysis) {
            llmAnalysis = await analyzeFraud({
                userEmail: user.email,
                ip,
                riskScore: riskAssessment.score,
                riskLevel: riskAssessment.level,
                failedAttempts: user.failedAttempts,
                accountStatus: user.status,
                factors: riskAssessment.factors,
                timestamp: new Date().toISOString(),
            });

            // If LLM says block, deny access — BUT still record the failed attempt
            if (
                llmAnalysis.recommendedAction === "block" ||
                llmAnalysis.recommendedAction === "suspend"
            ) {
                // Record the failed attempt so account status transitions properly
                const updatedUser = recordFailedAttempt(user, ip);
                return NextResponse.json(
                    {
                        error: "Login blocked by security analysis.",
                        riskScore: riskAssessment.score,
                        riskLevel: riskAssessment.level,
                        accountStatus: updatedUser.status,
                        failedAttempts: updatedUser.failedAttempts,
                        llmAnalysis: {
                            reasoning: llmAnalysis.reasoning,
                            action: llmAnalysis.recommendedAction,
                        },
                    },
                    { status: 403 }
                );
            }
        }

        // Check if account is locked
        if (user.status === "locked") {
            return NextResponse.json(
                {
                    error:
                        "Account is locked due to too many failed attempts. Please try again later.",
                    status: user.status,
                    accountStatus: "locked",
                    riskScore: riskAssessment.score,
                },
                { status: 403 }
            );
        }

        // Validate password
        const isValid = validatePassword(user, password);

        if (!isValid) {
            const updatedUser = recordFailedAttempt(user, ip);
            return NextResponse.json(
                {
                    error: "Invalid credentials.",
                    failedAttempts: updatedUser.failedAttempts,
                    accountStatus: updatedUser.status,
                    riskScore: riskAssessment.score,
                    riskLevel: riskAssessment.level,
                },
                { status: 401 }
            );
        }

        // Account is challenged — require extra verification (simplified: just warn)
        if (user.status === "challenged") {
            // In a real system, you'd send a 2FA code or CAPTCHA here
            // For this project, we allow login but flag it
            recordSuccessfulLogin(user, ip);
            return NextResponse.json({
                success: true,
                message: "Login successful. Note: Your account was under review.",
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    status: "active",
                },
                riskScore: riskAssessment.score,
                riskLevel: riskAssessment.level,
                wasChallended: true,
            });
        }

        // Successful login
        recordSuccessfulLogin(user, ip);
        return NextResponse.json({
            success: true,
            message: "Login successful!",
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                status: user.status,
            },
            riskScore: riskAssessment.score,
            riskLevel: riskAssessment.level,
            llmAnalysis: llmAnalysis
                ? { reasoning: llmAnalysis.reasoning }
                : null,
        });
    } catch (error) {
        console.error("Login API Error:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
