import { compare } from "bcryptjs";

import { getSql } from "@/lib/db.server";
import { verifySessionToken } from "@/lib/jwt.server";
import type { AdminRole, SessionPayload } from "@/lib/session.server";
import { SESSION_COOKIE } from "@/lib/session.server";

type UserRow = {
  id: string;
  email: string;
  password_hash: string;
  disabled_at: string | null;
};

export async function loadUserRoles(userId: string): Promise<AdminRole[]> {
  const sql = await getSql();
  const rows = await sql<{ role: AdminRole }[]>`
    SELECT role FROM admin_user_roles WHERE user_id = ${userId}::uuid
  `;
  return rows.map((r) => r.role);
}

export async function findUserByEmail(email: string): Promise<UserRow | null> {
  const sql = await getSql();
  const rows = await sql<UserRow[]>`
    SELECT id, email, password_hash, disabled_at
    FROM admin_users
    WHERE lower(email) = lower(${email})
    LIMIT 1
  `;
  return rows[0] ?? null;
}

export async function verifyCredentials(email: string, password: string): Promise<SessionPayload | null> {
  const user = await findUserByEmail(email.trim());
  if (!user || user.disabled_at) {
    return null;
  }
  const ok = await compare(password, user.password_hash);
  if (!ok) {
    return null;
  }
  const roles = await loadUserRoles(user.id);
  if (roles.length === 0) {
    return { id: user.id, email: user.email, roles: ["admin"] };
  }
  return { id: user.id, email: user.email, roles };
}

function parseCookie(header: string | null, name: string): string | null {
  if (!header) return null;
  for (const part of header.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}

export async function getSessionFromRequest(request: Request): Promise<SessionPayload | null> {
  const token = parseCookie(request.headers.get("cookie"), SESSION_COOKIE);
  if (!token) return null;
  return verifySessionToken(token);
}
