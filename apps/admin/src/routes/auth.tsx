import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { login } from "@/lib/auth.functions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
});

function AuthPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [carregando, setCarregando] = useState(false);

  const entrar = async () => {
    setCarregando(true);
    try {
      await login({ data: { email, password: senha } });
      toast.success("Bem-vindo(a)!");
      await navigate({ to: "/dash" });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-background p-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight">Ducadu Admin</h1>
        <p className="text-sm text-muted-foreground">admin.ducadu.com.br</p>
      </div>
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-lg">Entrar</CardTitle>
          <CardDescription>Acesso restrito à equipe Ducadu.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="email">E-mail</Label>
            <Input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="senha">Senha</Label>
            <Input
              id="senha"
              type="password"
              autoComplete="current-password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void entrar()}
            />
          </div>
          <Button className="w-full" onClick={() => void entrar()} disabled={carregando || !email || !senha}>
            {carregando && <Loader2 className="size-4 animate-spin" />}
            Entrar
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
