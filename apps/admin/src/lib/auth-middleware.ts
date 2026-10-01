import { createMiddleware } from "@tanstack/react-start";
import { getRequest } from "@tanstack/start-server-core/request-response";

import { getSessionFromRequest } from "@/lib/auth.server";
import type { SessionPayload } from "@/lib/session.server";

export const requireSession = createMiddleware({ type: "function" }).server(async ({ next }) => {
  const session = await getSessionFromRequest(getRequest());
  if (!session) {
    throw new Error("Unauthorized: sessão inválida ou expirada");
  }
  return next({
    context: {
      session,
    },
  });
});

export type SessionContext = {
  session: SessionPayload;
};
