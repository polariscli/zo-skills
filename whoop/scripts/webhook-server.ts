#!/usr/bin/env bun
/**
 * whoop webhook receiver
 * receives sleep.updated webhooks and triggers exploration
 */

import { createHmac } from "crypto";
import { spawn } from "child_process";

const PORT = 8081;
const CREDS_PATH = "/home/.z/whoop/credentials.json";
const EXPLORATION_AGENT_PATH = "/home/workspace/Skills/night-exploration/scripts/trigger.ts";

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
  const file = Bun.file(CREDS_PATH);
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
  
  // spawn exploration agent
  const proc = spawn("bun", [EXPLORATION_AGENT_PATH, sleepId], {
    detached: true,
    stdio: "ignore"
  });
  
  proc.unref();
  console.log(`exploration agent spawned (pid: ${proc.pid})`);
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
