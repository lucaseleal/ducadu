# Ducadu Admin (`admin.ducadu.com.br`)

Shell web (TanStack Start + shadcn) com login no **NeonDB** e **Dash Gerencial** em Streamlit embarcado via iframe.

## Pré-requisitos

1. Aplicar [`sql/003_admin_auth.sql`](../../sql/003_admin_auth.sql) no Neon.
2. Variáveis na raiz do repo (`.env`) ou em `apps/admin/.env`:

```env
DATABASE_URL=postgresql://...
SESSION_SECRET=uma-string-secreta-com-pelo-menos-32-caracteres
VITE_STREAMLIT_URL=http://localhost:8501

# Mesmo padrão do Lambda / Streamlit — evita IP allowlist do Neon no dev
CF_TUNNEL_HOSTNAME=...
CF_CLIENT_ID=...
CF_CLIENT_SECRET=...
```

3. **Cloudflare Access tunnel** (`CF_TUNNEL_*`) para scripts e `bun run dev`, como no `lambda/src/db.py`. Só WARP **não** substitui isso: conexão direta ao host Neon usa o IPv6 do WARP, que costuma **não** estar na allowlist do Neon (erro `28000`). No DBeaver, confira se o host é `127.0.0.1:15432` (tunnel) ou o hostname Neon.

Scripts e dev usam **PostgreSQL TCP** via tunnel quando `CF_TUNNEL_HOSTNAME` está definido. O deploy no Worker usa `@neondatabase/serverless` (HTTP).

## Bootstrap do primeiro admin

```powershell
cd c:\Users\luke2\Documents\ducadu\apps\admin
$env:ADMIN_BOOTSTRAP_EMAIL="admin@ducadu.com.br"
$env:ADMIN_BOOTSTRAP_PASSWORD="sua-senha-forte"
bun run bootstrap-user
```

## Dev local (dois processos)

| Processo | Comando | Porta |
|----------|---------|-------|
| Admin shell | `bun run dev` em `apps/admin` | 3000 |
| Streamlit | `uv run --project apps/ifood_homolog streamlit run apps/ifood_homolog/app.py` | **8501** (fixo em `.streamlit/config.toml`) |

O iframe usa `VITE_STREAMLIT_URL` (default `http://localhost:8501`). Se o Streamlit subir em **outra porta**, ajuste no `.env` da raiz e **reinicie** `bun run dev` (variáveis `VITE_*` são lidas na subida do Vite).

Abra http://localhost:3000 → login → **Dash Gerencial**.

### Onde ver o “backend” no dev

Não há API separada na porta 8080. O **TanStack Start** roda front + **server functions** no mesmo processo:

| O quê | Onde |
|-------|------|
| App | http://localhost:3000 |
| Logs de login / DB / tunnel | **Terminal** onde roda `bun run dev` (procure `[TUNNEL]` ou stack trace) |
| Chamada de login | DevTools → **Network** → filtro `login` ou `_server` → status e corpo da resposta |
| Toast na tela | Mensagem amigável (`E-mail ou senha inválidos`, `SESSION_SECRET…`, etc.) |

Reinicie `bun run dev` após mudar o `.env` da **raiz** (`DATABASE_URL`, `SESSION_SECRET`, `CF_TUNNEL_*`). O bootstrap lia esse `.env`; o dev server precisava do mesmo (agora carregamos a raiz automaticamente).

`favicon.ico` 404 e aviso do React DevTools são **ruído**, não causam falha de login.

## Build e deploy

```powershell
cd apps/admin
bun run build
bun run deploy
```

CI: [`.github/workflows/deploy_admin.yml`](../../.github/workflows/deploy_admin.yml).

Secrets GitHub: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `DATABASE_URL`, `SESSION_SECRET`, `VITE_STREAMLIT_URL`.

## Produção — Streamlit (pós-MVP)

O iframe aponta para `VITE_STREAMLIT_URL`. **Não** exponha o Streamlit publicamente sem proteção:

1. **Recomendado:** hospedar Streamlit em rede privada ou atrás de **Cloudflare Access** (mesma identidade WARP/SSO).
2. **Alternativa:** reverse proxy no mesmo hostname (`admin.ducadu.com.br/streamlit/*`) validando cookie de sessão do admin (implementação futura).
3. **Dev/homolog:** localhost + login no shell é suficiente para gravação de vídeos iFood (sidebar Streamlit continua mostrando `client_id` / UTC).

Até endurecer o passo 1–2, trate o login do admin como barreira operacional, não como isolamento criptográfico do iframe.

## Stack

- TanStack Start + Router + Query
- shadcn/ui + Tailwind 4 (oklch)
- Sessão JWT httpOnly (`ducadu_session`)
- Sem Supabase, sem Lovable
