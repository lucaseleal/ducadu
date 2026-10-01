# Dash gerencial — visão Cadu (metas por loja)

Especificação alinhada ao pedido de gestão **D-1**, substituindo a aba técnica “Analytics KPIs” por indicadores operacionais e **atingimento de meta** (4 eixos × 25%).

Referência de escopo geral: [`proposta-dashboard-ducadu.md`](proposta-dashboard-ducadu.md) (Fase 3 — Selo Super).

---

## O que a loja precisa ver

| Indicador | Número | % (meta) | Granularidade desejada | Fonte hoje | Status |
|-----------|--------|----------|------------------------|------------|--------|
| **Pedidos iFood (mês)** | Total de pedidos no canal | — | Mês; ideal D-1 por dia | Financial Sales / Analytics `orderStatus` / Neon `ifood_orders` | **Implementável** (mês + tendência diária via Analytics groupBy dia) |
| **Nota iFood (app)** | Nota exibida no app (referência) | — | Fixo portal (~**3 meses** rolling) | Review API `GET .../summary` | **Implementável** (rótulo “referência iFood 3m”) |
| **Nota iFood (meta Ducadu)** | Média das avaliações **no mês corrente** | vs meta (ex.: ≥ 4,7) | Mês | Review API lista + Neon `ifood_reviews` | **Implementável** (regra diferente do app) |
| **Cancelamentos** | Qtd cancelados | **%** sobre pedidos totais | Mês **e dia** | Analytics KPIs `orderStatus=CANCELLED` ou Financial + status | **Parcial** (validar paridade com Portal Selo) |
| **Chamados** | Qtd chamados / disputas | **%** sobre pedidos | Mês **e dia** | Selo ≈ Handshake / negociação — **confirmar com iFood** | **Pendente** (Anexo A proposta) |
| **NPS Falaê** | Nota pesquisa | vs meta | Mês | API Falaê + **rotina loja** (cupom/link pós-pedido) | **Pendente** (Fase 4) |
| **Nota nutricionista** | Nota auditoria | vs meta (25%) | Mês | Planilha / processo loja (não iFood) | **Pendente** (cadastro manual ou Sheets) |

**Score composto (meta loja):**

```text
atingimento_geral =
  0,25 × atingimento_nota_nutricionista
+ 0,25 × atingimento_cancelamentos   (quanto menor %, melhor)
+ 0,25 × atingimento_chamados        (quanto menor %, melhor)
+ 0,25 × atingimento_nota_ifood_mês  (quanto maior nota, melhor)
```

Cada eixo retorna **0–100%** de atingimento da meta configurada; eixos sem dado entram como “—” e não entram na média até existir fonte.

Metas (% ou nota mínima) devem ficar em **`dim_metas_loja`** (Sheets/Neon) por loja e mês — hoje o painel homolog usa inputs na sidebar só para protótipo.

---

## Regras de cálculo (proposta)

### Pedidos totais (visão iFood)

- **Numerador/denominador cancelamentos e chamados:** pedidos **iFood** no período (mesma base), não mix Saipos balcão.
- **Mês:** `referenceDate` ou `sales_date` entre 1º e último dia do mês (D-1: até ontem se mês corrente).
- **API:** `POST /analytics/v1.0/merchants/{id}/orders/kpis` com `groupBy: orderStatus` → contar `CONCLUDED`, `CANCELLED`, etc.

### Cancelamentos

- **Número:** pedidos com status cancelado no período (definição Selo a cruzar com Portal).
- **%:** `cancelados / (concluídos + cancelados + …)` — denominador explícito na tela.
- **Dia:** mesmo KPI com filtro de um dia ou groupBy data (quando homologado na API).

### Chamados

- Hipótese: eventos **Handshake / Negotiation** ou métrica Selo no Portal — **não assumir** sem resposta do gerente iFood (pergunta 2, Anexo A).
- Até lá: card “Chamados” com status **sem integração** e meta manual desabilitada no score.

### Nota iFood

- **Coluna “App iFood”:** `GET /review/v2.0/merchants/{id}/summary` (nota agregada oficial / visível).
- **Coluna “Meta Ducadu (mês)”:** média `rating`/`score` das reviews com `review_date` no mês — **não** misturar com janela de 3 meses do app.

### NPS Falaê

- Depende de: conta Falaê, API, e **processo na loja** (QR/cupom após pedido).
- Fora do iFood; entra na Fase 4 do roadmap.

### Nota nutricionista

- Processo interno Ducadu; entrada manual ou ingest Sheets (`dim_metas` / `fato_auditoria_nutri`).

---

## Homologação iFood vs produção

- App `apps/ifood_homolog` com `IFOOD_USE_HOMOLOGATION=true`: aba **Desempenho & metas** = **apenas iFood Merchant API** (Analytics + Review). Sem Saipos, sem Neon nesta aba, sem score de meta calculado.
- Cards **Falaê, nutricionista, chamados, nota mês Ducadu, 4×25%** = wireframe (`—`) para o time iFood não confundir com escopo homologado.
- Evidência Analytics: expander JSON `POST /orders/kpis`.
- Painel **produção** (homolog false): Neon `ifood_*`, metas e score conforme seções acima.

---

## Próximos passos técnicos (ordem sugerida)

1. **SQL:** `dim_metas_loja` (loja, mês, meta_cancel_pct, meta_chamados_pct, meta_nota_ifood, meta_nota_nutri, meta_nps_falae).
2. **Views:** `v_ifood_pedidos_mes`, `v_ifood_cancelamentos_mes`, `v_ifood_reviews_nota_mes`.
3. **Ingest:** garantir `ifood_order_events` / polling se chamados vierem de Order (a definir).
4. **Falaê:** descoberta API + amarração cupom na loja.
5. **Painel produção:** mesma aba no Streamlit pós-login admin; auto-refresh TV.

---

## Responsabilidade Ducadu (dados que não vêm da API)

- Definir **metas numéricas** por loja (% cancelados, % chamados, nota mínima).
- Rotina **Falaê** e **nota nutricionista** na operação.
- Validar **cancelamentos/chamados** vs Portal Selo antes de vincular bonus/equipe.
