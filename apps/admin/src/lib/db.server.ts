import { neon } from "@neondatabase/serverless";

import { createLocalPostgres } from "@/lib/local-postgres.server";
import { loadRootEnv } from "@/lib/load-root-env.server";

function useNeonHttpDriver(): boolean {
  if (process.env.DUCADU_DB_TCP === "1") return false;
  if (process.env.DUCADU_DB_TCP === "0") return true;
  return import.meta.env.PROD;
}

let tcpPromise: ReturnType<typeof createLocalPostgres> | undefined;

export async function getSql() {
  loadRootEnv();
  if (useNeonHttpDriver()) {
    const url = process.env.DATABASE_URL;
    if (!url) throw new Error("DATABASE_URL não definida");
    return neon(url);
  }
  if (!tcpPromise) {
    tcpPromise = createLocalPostgres(10);
  }
  return tcpPromise;
}
