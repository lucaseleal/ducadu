import { SignJWT, jwtVerify } from "jose";

import type { SessionPayload } from "@/lib/session.server";
import { sessionSecret } from "@/lib/session.server";

const encoder = new TextEncoder();

function key() {
  return encoder.encode(sessionSecret());
}

export async function signSessionToken(payload: SessionPayload, maxAgeSeconds: number): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${maxAgeSeconds}s`)
    .sign(key());
}

export async function verifySessionToken(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, key());
    const id = payload.id;
    const email = payload.email;
    const roles = payload.roles;
    if (typeof id !== "string" || typeof email !== "string" || !Array.isArray(roles)) {
      return null;
    }
    return {
      id,
      email,
      roles: roles.filter(
        (r): r is SessionPayload["roles"][number] =>
          r === "admin" || r === "funcionario" || r === "leitura",
      ),
    };
  } catch {
    return null;
  }
}
