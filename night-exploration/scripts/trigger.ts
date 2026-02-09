#!/usr/bin/env bun
/**
 * trigger night exploration
 * can be called by: whoop webhook, cron, manual
 */

import { spawn } from "child_process";

const TRIGGER_ID = process.argv[2] || `manual-${Date.now()}`;
const SKILL_DIR = "/home/workspace/Skills/night-exploration";
const EXPLORATION_INSTRUCTIONS = `${SKILL_DIR}/scripts/explorer.md`;

// configuration
const MAX_MINUTES = 120; // 2 hours max
const WORKSPACE = "/home/workspace/Projects";
const SUMMARY_DIR = "/home/workspace/Memory/explorations";

console.log(`\n=== night exploration triggered ===`);
console.log(`trigger_id: ${TRIGGER_ID}`);
console.log(`timestamp: ${new Date().toISOString()}\n`);

// validate trigger (for whoop integration)
const validateSleepTrigger = async (sleepId: string): Promise<boolean> => {
  // skip validation for manual/scheduled triggers
  if (sleepId.startsWith("manual") || sleepId.startsWith("scheduled") || sleepId === "test") {
    return true;
  }
  
  // for whoop sleep IDs, optionally validate via whoop skill
  try {
    const result = spawn("python", [
      "/home/workspace/Skills/whoop/scripts/whoop.py",
      "sleep-details",
      sleepId
    ]);
    
    return new Promise((resolve) => {
      result.on("close", (code) => {
        resolve(code === 0);
      });
      result.on("error", () => resolve(false));
    });
  } catch {
    // if whoop skill not available, proceed anyway
    console.log("whoop validation skipped (skill not available)");
    return true;
  }
};

// main exploration flow
const explore = async () => {
  const isValid = await validateSleepTrigger(TRIGGER_ID);
  
  if (!isValid) {
    console.log("trigger validation failed, skipping exploration");
    return;
  }
  
  console.log("trigger validated, beginning exploration...\n");
  
  // read exploration instructions
  try {
    const instructions = await Bun.file(EXPLORATION_INSTRUCTIONS).text();
    console.log("exploration instructions loaded");
  } catch {
    console.log("warning: could not load exploration instructions");
  }
  
  // log exploration start
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 16);
  const summaryPath = `${SUMMARY_DIR}/${timestamp}.md`;
  
  console.log(`exploration summary: ${summaryPath}`);
  console.log("\nstarting autonomous exploration session...");

  // launch exploration runner and wait for completion
  const explorationProcess = spawn("bash", [
    `${SKILL_DIR}/scripts/run-session.sh`,
    TRIGGER_ID,
    MAX_MINUTES.toString(),
    WORKSPACE
  ], {
    stdio: "pipe"
  });

  console.log("exploration mode: ACTIVE");
  console.log("autonomous learning window: OPEN");
  console.log(`max_duration: ${MAX_MINUTES}m`);
  console.log(`workspace: ${WORKSPACE}`);
  console.log("\n(exploration running...)\n");

  // when exploration completes, send summary via SMS
  explorationProcess.on("close", async (code) => {
    console.log(`\nexploration session ended (exit code: ${code})`);

    try {
      // wait a moment for summary to be written
      await new Promise(resolve => setTimeout(resolve, 2000));

      // read the summary file
      const summaryContent = await Bun.file(summaryPath).text();

      // send via zo/ask API with SMS delivery
      const token = process.env.ZO_CLIENT_IDENTITY_TOKEN;
      if (!token) {
        console.error("ZO_CLIENT_IDENTITY_TOKEN not set, skipping SMS");
        return;
      }

      const prompt = `send sms to user with this night exploration summary:\n\n${summaryContent}`;

      const response = await fetch("https://api.zo.computer/zo/ask", {
        method: "POST",
        headers: {
          "authorization": token,
          "content-type": "application/json"
        },
        body: JSON.stringify({ input: prompt })
      });

      if (response.ok) {
        console.log("✓ summary SMS queued");
      } else {
        console.error(`✗ SMS delivery failed: ${response.status}`);
      }
    } catch (error) {
      console.error("error sending summary SMS:", error);
    }
  });
};

explore().catch(console.error);
