export function renderErrorPage(): string {
  return `<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Erro — Ducadu Admin</title></head>
<body style="font-family:system-ui;padding:2rem;text-align:center">
<h1>Algo deu errado</h1>
<p>Tente recarregar a página.</p>
<a href="/">Voltar ao início</a>
</body></html>`;
}
