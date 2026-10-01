import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/_authenticated/inicio")({
  component: InicioPage,
});

function InicioPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Bem-vindo</h1>
      <p className="max-w-2xl text-muted-foreground">
        Protótipo do futuro <strong>admin.ducadu.com.br</strong>. Use{" "}
        <Link to="/dash" className="text-primary underline">
          Dash Gerencial
        </Link>{" "}
        para o painel Streamlit (iFood homologação e, depois, KPIs D-1 Saipos).
      </p>
      <ul className="list-inside list-disc text-sm text-muted-foreground">
        <li>Autenticação: usuários no Neon (`sql/003_admin_auth.sql`)</li>
        <li>Dev local: WARP + `DATABASE_URL` na raiz; Streamlit na porta 8501</li>
      </ul>
    </div>
  );
}
