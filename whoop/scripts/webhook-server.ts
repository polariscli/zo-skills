#!/usr/bin/env bun
/**
 * whoop webhook receiver
 * receives sleep.updated webhooks and triggers exploration
 * includes watchdog timer to prevent hangs
 */

import { createHmac } from "crypto";
import { spawn } from "child_process";
import { writeFileSync } from "fs";

const PORT = 8081;
const CREDS_PATH = "/home/.z/whoop/credentials.json";
const EXPLORATION_AGENT_PATH = "/home/workspace/Skills/night-exploration/scripts/trigger.ts";
const HEARTBEAT_FILE = "/dev/shm/whoop-webhook-heartbeat";
const HEARTBEAT_INTERVAL = 5000; // 5s
const HEARTBEAT_TIMEOUT = 30000; // 30s - restart if no heartbeat for 30s

interface Credentials {
  client_id: string;
  client_secret: string;
  webhook_secret: string;
}

interface WebhookPayload {
  user_id: number;
  id: string;
  type: string;
  trace_id: string;
}

function loadCredentials(): Credentials {
  const text = require('fs').readFileSync(CREDS_PATH, 'utf-8');
  return JSON.parse(text);
}

function validateSignature(
  timestamp: string,
  body: string,
  signature: string,
  secret: string
): boolean {
  const payload = timestamp + body;
  const calculated = createHmac("sha256", secret)
    .update(payload)
    .digest("base64");
  
  return calculated === signature;
}

async function triggerExploration(sleepId: string) {
  console.log(`triggering exploration for sleep ${sleepId}`);
  
  // spawn exploration agent with timeout
  const proc = spawn("bun", [EXPLORATION_AGENT_PATH, sleepId], {
    detached: true,
    stdio: "ignore",
    timeout: 60000 // 60s timeout
  });
  
  proc.unref();
  console.log(`exploration agent spawned (pid: ${proc.pid})`);
}

// heartbeat monitoring
function startHeartbeat() {
  setInterval(() => {
    const now = Date.now();
    try {
      writeFileSync(HEARTBEAT_FILE, now.toString());
    } catch (e) {
      console.error("heartbeat write failed:", e);
    }
  }, HEARTBEAT_INTERVAL);
  
  console.log("heartbeat monitor started");
}

// watchdog timer - monitor from parent process
function startWatchdog() {
  const checkInterval = setInterval(async () => {
    try {
      const response = await fetch("http://localhost:8081/health", {
        signal: AbortSignal.timeout(5000)
      });
      if (!response.ok) {
        console.error("health check failed, restarting...");
        process.exit(1);
      }
    } catch (error) {
      console.error("health check error, restarting:", error);
      process.exit(1);
    }
  }, HEARTBEAT_TIMEOUT);
  
  // don't keep process alive for this interval
  checkInterval.unref?.();
  console.log("watchdog timer started");
}

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    
    // health check
    if (url.pathname === "/health") {
      return new Response("ok", { status: 200 });
    }
    
    // webhook endpoint
    if (url.pathname === "/webhook" && req.method === "POST") {
      try {
        const creds = loadCredentials();
        
        // validate signature
        const signature = req.headers.get("x-whoop-signature");
        const timestamp = req.headers.get("x-whoop-signature-timestamp");
        const body = await req.text();
        
        if (!signature || !timestamp) {
          console.log("missing signature headers");
          return new Response("missing signature", { status: 401 });
        }
        
        if (!validateSignature(timestamp, body, signature, creds.webhook_secret)) {
          console.log("invalid signature");
          return new Response("invalid signature", { status: 401 });
        }
        
        // parse payload
        const payload: WebhookPayload = JSON.parse(body);
        console.log(`received webhook: ${payload.type} for user ${payload.user_id}`);
        
        // handle sleep.updated events
        if (payload.type === "sleep.updated") {
          await triggerExploration(payload.id);
        }
        
        return new Response("ok", { status: 200 });
      } catch (error) {
        console.error("webhook error:", error);
        return new Response("error", { status: 500 });
      }
    }
    
    return new Response("not found", { status: 404 });
  }
});

console.log(`whoop webhook server listening on port ${PORT}`);
console.log(`webhook endpoint: http://localhost:${PORT}/webhook`);
console.log(`health check: http://localhost:${PORT}/health`);

startHeartbeat();
startWatchdog();
