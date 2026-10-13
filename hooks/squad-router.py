#!/usr/bin/env python3
"""UserPromptSubmit: points to the squad agent when the request matches a role.

Meant to sit next to a design skill router, if you run one. Prints at most 2
lines and stays silent when nothing matches. `developer` has no trigger on
purpose: it would match almost every request; the table in the global
CLAUDE.md covers that case.

The patterns are bilingual on purpose (Portuguese and English): owners type in
any language. The prompt is lowercased and stripped of accents before matching.
"""
import json
import re
import sys
import unicodedata

def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

# Order matters: the specific comes before the generic.
RULES = [
    (r"\b(terraform|tfstate|iam\b|vpc\b|pipeline|ci/cd|github actions|workflow do ci|ci workflow|dockerfile|docker-compose|deploy|provisionar|provision|infraestrutura|infrastructure)",
     "infra -> `infra` agent (writes and validates, stops at plan; never apply/deploy)."),

    (r"\b(quanto custa|custo mensal|custo de|cotar|cotacao|fatura|billing|finops|gasto de tokens|custo de tokens|quanto gastamos|onde cortar"
     r"|how much does|monthly cost|cost of|cost estimate|price quote|invoice|token spend|token cost|how much (did|have) we spen|where to cut)",
     "cost -> `finops` agent (cloud with source and date; tokens through `agenfk tokens`)."),

    (r"\b(precific|preco do plano|pagina de preco|margem|economia unitaria|unit economics|ponto de equilibrio|break-?even|runway|receita|investidor"
     r"|pricing|plan price|profit margin|gross margin|margin per|revenue|investor)",
     "finance -> `finance` agent (numbers with a source; without data, returns what is missing)."),

    (r"\b(concorrente|posicionamento|go-to-market|gtm\b|pitch|primeiros clientes|cliente ideal|icp\b|como vender|abordagem comercial|prospec"
     r"|competitor|positioning|first customers|ideal customer|how to sell|sales approach|outreach|prospect)",
     "go-to-market -> `gtm` agent (drafts only; never sends or publishes)."),

    (r"\b(quanto falta|proximo bloco|proximo passo do projeto|priorizar|prioridade|replanejar|roadmap|decompor|epico|epic\b|planejar a semana|em qual projeto"
     r"|how much is left|next block|next step (of|for) the project|prioriti[sz]e|priority|replan|break down into cards|decompose|plan the week|which project)",
     "product -> `product` agent (real state of the repo, smallest increment, cards in AgenFK)."),

    (r"\b(revis[ae]r? (a |essa |esta )?(pr|pull request)\b|o que (essa|esta|a) (pr|pull request) faz|resum[eo] da (pr|pull request)\b"
     r"|review (this |the )?(pr|pull request)\b|what does (this|the) (pr|pull request) do|summari[sz]e (this|the) (pr|pull request)\b)",
     "open PR review -> `pull-request-reviewer` agent (DeepSeek flash via `pr-review`; prints what the PR does and the findings; never posts)."),

    (r"\b(revisao independente|verificar a branch|verificador|mutacao|mutation|antes do pr|antes de abrir o pr|pode mergear|esta pronto para merge"
     r"|independent review|verify the branch|verifier|before the pr|before opening the pr|can i merge|ready to merge)",
     "verification -> `verifier` agent (clean context, mutation, SHIP/FIX_FIRST/REJECT)."),

    (r"\b(escrever testes|escreva testes|cobertura|teste de regressao|testes do card|falta teste"
     r"|write tests|coverage|regression test|tests for the card|card'?s tests|missing tests?)",
     "tests -> `tester` agent (Sonnet; proof by mutation; records with `agenfk log-test`)."),

    (r"\b(worktree|pilha de pr|stack de pr|mergear|merge\b|rebase|branch(es)? (aberta|morta|orfa)|paraleliz|em paralelo|varias sessoes|quem esta onde|o que esta aberto"
     r"|pr stack|stacked prs?|(open|dead|stale|orphan(ed)?) branch(es)?|paralleli[sz]|in parallel|several sessions|multiple sessions|who is where|what is open|what's open)",
     "git/parallelism -> `github` agent (map session->worktree->branch->card->PR; disjoint fronts; merge train as a proposal; never merges)."),

    (r"\b(handoff|hand-off|contexto cheio|compact|/clear|de onde parei|retomar|em loop|loop\b|gastando muito|burn|releitura|trocar de card|fechar o dia|encerrar por hoje"
     r"|full context|context is full|where did i stop|where was i|resume|pick up where|in a loop|spending too much|reread|switch(ing)? cards?|close the day|done for today|call it a day)",
     "context -> `context` agent (Sonnet; measures ctx/burn/reread/loop with session_context.py; decides compact|handoff|cut the loop; switches between cards)."),

    (r"\b(tela|pagina|landing|dashboard|componente|interface|ui\b|ux\b|design|figma|design tokens?|tokens? de design|dark mode|animacao|motion|poster|banner|logo|icone|arte|canvas|visual"
     r"|screen|page\b|component|animation|icons?\b|art\b|artwork)",
     "interface/visual -> `frontend` agent (loads `design-reference` + at most 1 design skill; direction before code; measured quality floor)."),
]

MAX_HINTS = 2

def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = norm(str(payload.get("prompt") or ""))
    if not prompt:
        return 0
    hints = [hint for pattern, hint in RULES if re.search(pattern, prompt)]
    for hint in hints[:MAX_HINTS]:
        print("[squad route] " + hint)
    if hints:
        print("A project-specific agent for the same role takes priority; pass the AgenFK card id.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
