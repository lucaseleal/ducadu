/**
 * Conexão local ao Neon — espelha lambda/src/db.py (cloudflared access tcp).
 */
import { spawn, type ChildProcess } from "node:child_process";
import { createConnection } from "node:net";
import postgres from "postgres";

const PROXY_PORT = 15432;

let cfProc: ChildProcess | null = null;
let tunnelSpawnedByUs = false;

function cloudflaredBin(): string {
  return "cloudflared";
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

async function isPortOpen(port: number): Promise<boolean> {
  try {
    await new Promise<void>((resolve, reject) => {
      const s = createConnection({ host: "127.0.0.1", port }, () => {
        s.destroy();
        resolve();
      });
      s.on("error", reject);
    });
    return true;
  } catch {
    return false;
  }
}

async function waitForPort(port: number, deadlineMs: number): Promise<void> {
  const deadline = Date.now() + deadlineMs;
  while (Date.now() < deadline) {
    if (await isPortOpen(port)) return;
    await sleep(300);
  }
  throw new Error(`cloudflared não ficou pronto na porta ${port} em ${deadlineMs}ms`);
}

export async function ensureCloudflareTunnel(): Promise<void> {
  const hostname = process.env.CF_TUNNEL_HOSTNAME;
  if (!hostname) return;

  if (await isPortOpen(PROXY_PORT)) {
    console.log(`[TUNNEL] proxy já ativo em 127.0.0.1:${PROXY_PORT}`);
    return;
  }

  if (cfProc && cfProc.exitCode === null) {
    await waitForPort(PROXY_PORT, 2000);
    return;
  }

  cfProc = spawn(
    cloudflaredBin(),
    [
      "access",
      "tcp",
      "--hostname",
      hostname,
      "--url",
      `localhost:${PROXY_PORT}`,
      "--service-token-id",
      process.env.CF_CLIENT_ID ?? "",
      "--service-token-secret",
      process.env.CF_CLIENT_SECRET ?? "",
    ],
    { stdio: "ignore", shell: true, windowsHide: true },
  );
  tunnelSpawnedByUs = true;

  cfProc.on("error", (err) => {
    throw new Error(
      `Não foi possível iniciar cloudflared (${err.message}). Instale cloudflared e confira CF_TUNNEL_* no .env.`,
    );
  });

  await waitForPort(PROXY_PORT, 10_000);
  console.log(`[TUNNEL] cloudflared pronto em 127.0.0.1:${PROXY_PORT}`);
}

/** Encerra cloudflared iniciado por este processo (scripts one-shot). */
export function shutdownTunnelIfOwned(): void {
  if (!tunnelSpawnedByUs || !cfProc) return;
  try {
    cfProc.kill();
  } catch {
    /* ignore */
  }
  cfProc = null;
  tunnelSpawnedByUs = false;
}

function stripUriParam(url: string, param: string): string {
  let u = url;
  u = u.replace(new RegExp(`&${param}=[^&]*`, "g"), "");
  u = u.replace(new RegExp(`\\?${param}=[^&]*&`, "g"), "?");
  u = u.replace(new RegExp(`\\?${param}=[^&]*$`, "g"), "");
  return u;
}

/** URL TCP para postgres.js — tunnel local ou DATABASE_URL direto. */
export function resolvePostgresUrl(): string {
  const dbUrl = process.env.DATABASE_URL;
  if (!dbUrl) {
    throw new Error("DATABASE_URL não definida");
  }
  if (!process.env.CF_TUNNEL_HOSTNAME) {
    return dbUrl;
  }

  const hostMatch = dbUrl.match(/@([^/?:]+)/);
  const endpointId = hostMatch?.[1]?.split(".")[0] ?? "";

  let url = dbUrl.replace(/@[^/?]+/, `@127.0.0.1:${PROXY_PORT}`);
  url = stripUriParam(url, "channel_binding");
  url = stripUriParam(url, "options");

  const encodedEndpoint = encodeURIComponent(`endpoint=${endpointId}`);
  const join = url.includes("?") ? "&" : "?";
  return `${url}${join}options=${encodedEndpoint}`;
}

export async function createLocalPostgres(max = 1) {
  await ensureCloudflareTunnel();
  const url = resolvePostgresUrl();
  return postgres(url, { ssl: "require", max });
}
