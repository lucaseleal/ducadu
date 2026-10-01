import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { BarChart3, Shield } from "lucide-react";

import { getSession } from "@/lib/auth.functions";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export const Route = createFileRoute("/")({
  component: IndexPage,
});

function IndexPage() {
  const navigate = useNavigate();

  useEffect(() => {
    void getSession().then((session) => {
      if (session) void navigate({ to: "/inicio", replace: true });
    });
  }, [navigate]);

  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <span className="text-lg font-semibold tracking-tight">Ducadu Admin</span>
        <Button asChild size="sm">
          <Link to="/auth">Entrar</Link>
        </Button>
      </header>

      <main className="mx-auto max-w-6xl px-4 pb-20">
        <section className="py-14 sm:py-20">
          <p className="text-sm font-medium uppercase tracking-widest text-primary">Gestão D-1</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
            Indicadores e homologações iFood em um só lugar.
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            Login seguro no NeonDB. Dash gerencial em Streamlit embarcado. Próximas telas nativas
            React conforme a proposta Ducadu.
          </p>
          <div className="mt-8">
            <Button asChild size="lg">
              <Link to="/auth">Acessar painel</Link>
            </Button>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardContent className="pt-6">
              <BarChart3 className="size-5 text-primary" />
              <h2 className="mt-3 font-semibold">Dash Gerencial</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Conciliação iFood, KPIs Analytics e Review (homologação read-only).
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <Shield className="size-5 text-primary" />
              <h2 className="mt-3 font-semibold">Acesso restrito</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Usuários e papéis no Neon — sem Supabase.
              </p>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}
