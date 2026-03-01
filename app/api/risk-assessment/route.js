import { NextResponse } from "next/server";
const { calculateRiskScore } = require("@/lib/riskEngine");
const { analyzeFraud } = require("@/lib/llmClient");
const { findUserByEmailOrPhone } = require("@/lib/users");

export async function POST(request) {
    try {
        const body = await request.json();
        const { email, ip } = body;

        const user = findUserByEmailOrPhone(email);
        const userAgent = request.headers.get("user-agent") || "Unknown";

        const riskAssessment = calculateRiskScore({
            user: user || {
                knownIPs: [],
                failedAttempts: 0,
                status: "active",
            },
            ip: ip || "0.0.0.0",
            userAgent,
            timestamp: new Date(),
        });

        let llmAnalysis = null;
        if (riskAssessment.requiresLLMAnalysis) {
            llmAnalysis = await analyzeFraud({
                userEmail: email,
                ip: ip || "0.0.0.0",
                riskScore: riskAssessment.score,
                riskLevel: riskAssessment.level,
                failedAttempts: user ? user.failedAttempts : 0,
                accountStatus: user ? user.status : "unknown",
                factors: riskAssessment.factors,
                timestamp: new Date().toISOString(),
            });
        }

        return NextResponse.json({
            riskScore: riskAssessment.score,
            riskLevel: riskAssessment.level,
            factors: riskAssessment.factors,
            recommendation: riskAssessment.recommendation,
            llmAnalysis,
        });
    } catch (error) {
        console.error("Risk Assessment API Error:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
