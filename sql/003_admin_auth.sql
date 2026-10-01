-- Admin web app (admin.ducadu.com.br) — usuários e papéis no NeonDB.

CREATE TYPE admin_app_role AS ENUM ('admin', 'funcionario', 'leitura');

CREATE TABLE IF NOT EXISTS admin_users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS admin_user_roles (
    user_id UUID NOT NULL REFERENCES admin_users (id) ON DELETE CASCADE,
    role    admin_app_role NOT NULL,
    PRIMARY KEY (user_id, role)
);

CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users (email);

COMMENT ON TABLE admin_users IS 'Login do painel admin Ducadu (TanStack Start).';
COMMENT ON TABLE admin_user_roles IS 'Papéis por usuário — espelho conceitual do app de obras.';
