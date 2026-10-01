import { createFileRoute } from "@tanstack/react-router";

import { streamlitUrl } from "@/lib/env";

export const Route = createFileRoute("/_authenticated/dash")({
  component: DashPage,
});

function DashPage() {
  const src = streamlitUrl();

  return (
    <div className="space-y-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dash Gerencial</h1>
        <p className="text-sm text-muted-foreground">
          Streamlit embarcado — homologação iFood (Financial, Analytics, Review).
        </p>
      </div>
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <iframe
          title="Dash Gerencial Streamlit"
          src={src}
          className="h-[calc(100vh-14rem)] w-full min-h-[480px] border-0"
          allow="clipboard-read; clipboard-write"
        />
      </div>
      <p className="text-xs text-muted-foreground">
        Origem do iframe: <code className="rounded bg-muted px-1">{src}</code>
        {" — "}
        deve ser a mesma URL do Streamlit no navegador. Padrão{" "}
        <code className="rounded bg-muted px-1">8501</code> (ver{" "}
        <code className="rounded bg-muted px-1">apps/ifood_homolog/.streamlit/config.toml</code>
        ). Se usar outra porta, defina{" "}
        <code className="rounded bg-muted px-1">VITE_STREAMLIT_URL</code> no{" "}
        <code className="rounded bg-muted px-1">.env</code> da raiz e reinicie{" "}
        <code className="rounded bg-muted px-1">bun run dev</code>.
      </p>
      <p className="text-xs text-muted-foreground">
        Subir Streamlit:{" "}
        <code className="rounded bg-muted px-1">
          uv run --project apps/ifood_homolog streamlit run apps/ifood_homolog/app.py
        </code>
      </p>
    </div>
  );
}
