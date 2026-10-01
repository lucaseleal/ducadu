import { createServerFn } from "@tanstack/react-start";
import {
  deleteCookie,
  getRequest,
  setCookie,
} from "@tanstack/start-server-core/request-response";

import { getSessionFromRequest, verifyCredentials } from "@/lib/auth.server";
import { signSessionToken } from "@/lib/jwt.server";
import { cookieOptions, SESSION_COOKIE } from "@/lib/session.server";

const SESSION_MAX_AGE = 60 * 60 * 24 * 7;

export const getSession = createServerFn({ method: "GET" }).handler(async () => {
  const { loadRootEnv } = await import("@/lib/load-root-env.server");
  loadRootEnv();
  const request = getRequest();
  return getSessionFromRequest(request);
});

export const login = createServerFn({ method: "POST" })
  .validator((data: { email: string; password: string }) => {
    if (!data.email?.trim() || !data.password) {
      throw new Error("Informe e-mail e senha.");
    }
    return data;
  })
  .handler(async ({ data }) => {
    const { loadRootEnv } = await import("@/lib/load-root-env.server");
    loadRootEnv();
    const session = await verifyCredentials(data.email, data.password);
    if (!session) {
      throw new Error("E-mail ou senha inválidos.");
    }
    const token = await signSessionToken(session, SESSION_MAX_AGE);
    setCookie(SESSION_COOKIE, token, cookieOptions(SESSION_MAX_AGE));
    return session;
  });

export const logout = createServerFn({ method: "POST" }).handler(async () => {
  deleteCookie(SESSION_COOKIE, { path: "/" });
  return { ok: true as const };
});
