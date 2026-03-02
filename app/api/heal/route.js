import { NextResponse } from "next/server";
const { repairSelector, resolveInteractionBlocker } = require("@/lib/llmClient");

export async function POST(request) {
    try {
        const body = await request.json();
        const { oldSelector, domSnippet, elementDescription, taskType, actionDescription } = body;

        if (!domSnippet) {
            return NextResponse.json(
                { error: "domSnippet is required" },
                { status: 400 }
            );
        }

        let result;
        if (taskType === "interaction_unblock") {
            result = await resolveInteractionBlocker(
                oldSelector || "unknown",
                domSnippet,
                actionDescription || elementDescription || "Recover blocked click"
            );
        } else {
            if (!oldSelector) {
                return NextResponse.json(
                    { error: "oldSelector is required for selector repair" },
                    { status: 400 }
                );
            }
            result = await repairSelector(
                oldSelector,
                domSnippet,
                elementDescription || "Unknown element"
            );
        }

        return NextResponse.json({
            success: true,
            ...result,
        });
    } catch (error) {
        console.error("Heal API Error:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
