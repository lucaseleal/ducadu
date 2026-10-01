/**
 * Cria usuário admin no Neon (após aplicar sql/003_admin_auth.sql).
 */
import { hash } from "bcryptjs";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

import {
  createLocalPostgres,
  shutdownTunnelIfOwned,
} from "../src/lib/local-postgres.server.ts";

function loadRootEnv() {
  const rootEnv = resolve(import.meta.dir, "../../../.env");
  if (!existsSync(rootEnv)) return;
  for (const line of readFileSync(rootEnv, "utf-8").split("\n")) {
    const t = line.trim();
    if (!t || t.startsWith("#") || !t.includes("=")) continue;
    const [k, ...rest] = t.split("=");
    const key = k?.trim();
    if (!key || process.env[key]) continue;
    process.env[key] = rest.join("=").trim();
  }
}

async function main(): Promise<number> {
  loadRootEnv();

  const email = process.env.ADMIN_BOOTSTRAP_EMAIL?.trim();
  const password = process.env.ADMIN_BOOTSTRAP_PASSWORD;

  if (!email || !password) {
    console.error("Defina ADMIN_BOOTSTRAP_EMAIL e ADMIN_BOOTSTRAP_PASSWORD");
    return 1;
  }

  const sql = await createLocalPostgres(1);
  const passwordHash = await hash(password, 12);

  try {
    const existing = await sql`
      SELECT id FROM admin_users WHERE lower(email) = lower(${email}) LIMIT 1
    `;
    if (existing.length > 0) {
      console.log("Usuário já existe:", email);
      return 0;
    }

    const inserted = await sql`
      INSERT INTO admin_users (email, password_hash)
      VALUES (${email}, ${passwordHash})
      RETURNING id
    `;
    const userId = inserted[0]?.id;
    if (!userId) {
      console.error("Falha ao inserir usuário");
      return 1;
    }

    await sql`
      INSERT INTO admin_user_roles (user_id, role)
      VALUES (${userId}::uuid, 'admin'::admin_app_role)
    `;

    console.log("Admin criado:", email);
    return 0;
  } finally {
    await sql.end({ timeout: 5 });
    shutdownTunnelIfOwned();
  }
}

const code = await main();
process.exit(code);
