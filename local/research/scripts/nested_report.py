"""Report of the nested-theme decisions (nested_apply.py final -> nested_decision.csv) for the customer: every row shows both themes.
Sections: strategy 2; strategy 1 by the meaning check; strategy 1 by rule (а) (checks said «same», the broad theme fails the selection);
customer decisions. With CRIT_AFTER (json of quiz_select criteria after the removals) also the final list: themes kept by strategy 1 that
have no statement and pass the selection after the removals — candidates for new statements.
-> local/research/theme_overlap/STRATEGIES.md
"""
import csv, json, os, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
O = f"{ROOT}/local/research/theme_overlap"
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
K = pd.read_csv(f"{O}/nested_decision.csv", dtype={"small_d": str, "big_d": str})
st = {r["d"]: r["q"] for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
lab = LB.load(nested=False)
D = {r["n"]: r["name_ru"] for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in lab["split_plan"]["new"].items(): D[k] = v.get("name_ru") or v["name_en"]
nm = lambda d: (f"[q{st[d]}] " if d in st else "") + D.get(d, d).split(" (+")[0]
BAS = {"two checks": "2 проверки", "third check": "3-я проверка", "customer": "решение заказчика"}
def table(df):
    L = ["| # | Узкая тема (законопр.) | Широкая тема (законопр.) | % узкой в широкой | Основание |", "|---|---|---|---|---|"]
    for i, r in enumerate(df.sort_values("pct_small", ascending=False).itertuples(), 1):
        L.append(f"| {i} | {nm(r.small_d)} ({r.n_small}) | {nm(r.big_d)} ({r.n_big}) | {r.pct_small:.0%} | {BAS.get(r.basis, r.basis)} |")
    return L
K.loc[K.customer, "basis"] = "customer"
cust = K[K.customer]
was_unres = set()
if os.path.exists(f"{O}/v1/nested_decision.csv"):
    v1 = pd.read_csv(f"{O}/v1/nested_decision.csv"); was_unres = set(v1[v1.decision == "unresolved"].pid)
unres = K[K.pid.isin(was_unres) & ~K.customer]
rest = K[~K.customer & ~K.pid.isin(was_unres)]
s2 = rest[rest.strategy == 2]; s1 = rest[(rest.strategy == 1) & ~rest.rule_a]; s1a = rest[(rest.strategy == 1) & rest.rule_a]
out = ["# Вложенные темы: стратегии по парам (проверка v1, третья секция актуализирована)", "",
       "Пара — узкая тема и широкая тема, в которой лежит не меньше 50 % законопроектов узкой. Тест проверки: может ли обычный избиратель "
       "согласиться с одной темой и не согласиться с другой. Да — стратегия 1 (узкая остаётся, общие законопроекты вычитаются из широкой); "
       "нет — стратегия 2 (общие законопроекты вычитаются из узкой). [qN] — у темы есть вопрос квиза.", "",
       f"## 1. Стратегия 2 — вычесть из узкой ({len(s2)} пар)", ""] + table(s2) + ["",
       f"## 2. Стратегия 1 — вычесть из широкой: проверка сочла темы разными ({len(s1)} пар)", ""] + table(s1) + ["",
       f"## 3. Стратегия 1 по правилу (а): проверка сочла темы одним вопросом, но широкая тема не проходит порог ({len(s1a)} пар)", "",
       "Узкая тема остаётся, потому что её законопроектам некуда уйти: по широкой теме вопроса нет и не будет.", ""] + table(s1a) + ["",
       f"## 4. Бывшие «не решено» — решены третьей проверкой ({len(unres)} пар)", "",
       "Первые две проверки разошлись; третья (выбор из двух) теперь решает ничью. Широкая тема не проходит порог → стратегия 1 по правилу (а).", "",
       "| # | Узкая тема (законопр.) | Широкая тема (законопр.) | % | Голоса (1-я / 2-я / 3-я) | Стратегия |", "|---|---|---|---|---|---|"] + \
      [f"| {i} | {nm(r.small_d)} ({r.n_small}) | {nm(r.big_d)} ({r.n_big}) | {r.pct_small:.0%} | {r.vA} / {r.vB} / {r.vC} | {int(r.strategy)}{' (правило (а))' if r.rule_a else ''} |"
       for i, r in enumerate(unres.sort_values("pct_small", ascending=False).itertuples(), 1)] + ["",
       f"## 5. Решения заказчика ({len(cust)} пар)", ""] + table(cust)
if os.environ.get("CRIT_AFTER"):
    A = json.load(open(os.environ["CRIT_AFTER"]))
    pl = json.load(open(f"{ROOT}/jef/directions/split/plan.json"))
    rem = (set(pl["parents"]) - set(pl["keep"])) | {d for p in LB.later_plans() for d in p["parents"]}
    tech = {"107", "128", "236", "289", "339", "343", "346"}
    kept = sorted(set(K[K.strategy == 1].small_d))
    new = [d for d in kept if d not in st and d not in rem and d not in tech and (A.get(d) or {}).get("base")]
    out += ["", f"## 6. Кандидаты в новые вопросы: остаются по стратегии 1, вопроса нет, после вычитаний проходят порог ({len(new)})", "",
            "| # | Тема | Законопроектов | Разброс | Списков |", "|---|---|---|---|---|"]
    out += [f"| {i} | {D.get(d, d)} | {A[d]['nA']} | {A[d]['sd']:.2f} | {A[d]['lists']} |" for i, d in enumerate(sorted(new, key=lambda d: -A[d]["nA"]), 1)]
open(f"{O}/STRATEGIES.md", "w").write("\n".join(out) + "\n")
print(len(s2), len(s1), len(s1a), len(cust))
