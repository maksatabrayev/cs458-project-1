import { NextResponse } from "next/server";
const { repairSelector } = require("@/lib/llmClient");

export async function POST(request) {
    try {
        const body = await request.json();
        const { oldSelector, domSnippet, elementDescription } = body;

        if (!oldSelector || !domSnippet) {
            return NextResponse.json(
                { error: "oldSelector and domSnippet are required" },
                { status: 400 }
            );
        }

        const result = await repairSelector(
            oldSelector,
            domSnippet,
            elementDescription || "Unknown element"
        );

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
