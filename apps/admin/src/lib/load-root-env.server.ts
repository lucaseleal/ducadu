import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

/** Carrega `.env` da raiz do monorepo (vite dev não lê só apps/admin). */
export function loadRootEnv(): void {
  if (process.env.DUCADU_ROOT_ENV_LOADED === "1") return;

  const candidates = [
    resolve(process.cwd(), ".env"),
    resolve(process.cwd(), "../.env"),
    resolve(process.cwd(), "../../.env"),
    resolve(import.meta.dirname, "../../../../.env"),
  ];

  for (const envPath of candidates) {
    if (!existsSync(envPath)) continue;
    for (const line of readFileSync(envPath, "utf-8").split("\n")) {
      const t = line.trim();
      if (!t || t.startsWith("#") || !t.includes("=")) continue;
      const [k, ...rest] = t.split("=");
      const key = k?.trim();
      if (!key || process.env[key] !== undefined) continue;
      process.env[key] = rest.join("=").trim();
    }
    process.env.DUCADU_ROOT_ENV_LOADED = "1";
    return;
  }
}
