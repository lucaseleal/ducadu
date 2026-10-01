import { useQuery } from "@tanstack/react-query";

import { getSession } from "@/lib/auth.functions";
import type { AdminRole } from "@/lib/session.server";

export type Perfil = {
  roles: AdminRole[];
  isAdmin: boolean;
  isStaff: boolean;
  somenteLeitura: boolean;
};

function derivarPerfil(roles: AdminRole[]): Perfil {
  const isAdmin = roles.includes("admin");
  const isStaff = isAdmin || roles.includes("funcionario");
  return { roles, isAdmin, isStaff, somenteLeitura: !isStaff };
}

export function usePerfil() {
  const query = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      const session = await getSession();
      if (!session) return derivarPerfil([]);
      return derivarPerfil(session.roles);
    },
    staleTime: 60_000,
  });
  return {
    perfil: query.data ?? derivarPerfil([]),
    session: query.data,
    carregando: query.isLoading,
    refetch: query.refetch,
  };
}

export function useSessionUser() {
  return useQuery({
    queryKey: ["session", "user"],
    queryFn: () => getSession(),
    staleTime: 60_000,
  });
}
