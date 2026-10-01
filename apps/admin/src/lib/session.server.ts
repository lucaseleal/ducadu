export const SESSION_COOKIE = "ducadu_session";

export type AdminRole = "admin" | "funcionario" | "leitura";

export type SessionUser = {
  id: string;
  email: string;
  roles: AdminRole[];
};

export type SessionPayload = SessionUser;

export function sessionSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error("SESSION_SECRET deve ter ao menos 32 caracteres");
  }
  return secret;
}

export function cookieOptions(maxAgeSeconds: number) {
  const secure = process.env.NODE_ENV === "production";
  return {
    httpOnly: true,
    secure,
    sameSite: "lax" as const,
    path: "/",
    maxAge: maxAgeSeconds,
  };
}
