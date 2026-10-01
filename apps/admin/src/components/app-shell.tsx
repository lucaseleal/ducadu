import { Link, useNavigate } from "@tanstack/react-router";
import { LayoutDashboard, LogOut, Home } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { logout } from "@/lib/auth.functions";
import { useSessionUser } from "@/lib/perfil";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/inicio", label: "Início", icon: Home },
  { to: "/dash", label: "Dash Gerencial", icon: LayoutDashboard },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: user } = useSessionUser();

  const sair = async () => {
    await logout();
    queryClient.clear();
    await navigate({ to: "/auth", replace: true });
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-card/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
          <Link to="/inicio" className="font-semibold tracking-tight text-foreground">
            Ducadu Admin
          </Link>
          <span className="text-xs text-muted-foreground">admin.ducadu.com.br</span>

          <div className="ml-auto flex items-center gap-2">
            {user && (
              <span className="hidden text-sm text-muted-foreground sm:inline">{user.email}</span>
            )}
            <Button variant="ghost" size="sm" onClick={() => void sair()} aria-label="Sair">
              <LogOut className="size-4" />
              Sair
            </Button>
          </div>

          <nav className="order-last flex w-full gap-1 overflow-x-auto pt-1 md:order-none md:w-auto md:pt-0">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground [&.active]:bg-primary/10 [&.active]:text-primary"
                activeProps={{ className: "active bg-primary/10 text-primary" }}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
