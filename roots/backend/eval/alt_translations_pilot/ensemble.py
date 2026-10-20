import json, sys, os, collections
sys.path.insert(0, sys.argv[1]); from alt_translations_ai import TRANSLATORS
D = sys.argv[2]; A, B = "glm-5.3", "deepseek-v4-pro"
NAMES = dict(TRANSLATORS); NAMES[0] = "PLANTED"
R = {}
for m in (A, B):
    for l in open(f"{D}/pilot_{m}.jsonl"):
        r = json.loads(l)
        if "result" in r: R[(m, r["job"])] = r

def fid_sum(j, rid):
    t = 0
    for m in (A, B):
        r = R[(m, j)]; inv = {v: k for k, v in r["letters"].items()}
        t += r["result"]["scores"].get(inv.get(rid), {}).get("fidelity", 0) or 0
    return t

def ensemble(j):
    ra, rb = R[(A, j)], R[(B, j)]
    ta, tb = ra["result"]["value"], rb["result"]["value"]
    hi, lo = max(ta, tb), min(ta, tb)
    tier = hi if hi >= 2 else lo
    review = False
    if tier == 3 and lo < 2:
        tier, review = 2, True
    elif tier == 3:
        review = True  # auto-shown, but also a fix candidate for our translation
    if ta != tb:
        lead = ra if ta > tb else rb
    else:
        lead = max((ra, rb), key=lambda r: fid_sum(j, r["best_rid"]))
    return dict(job=j, tier=tier, review=review, best=NAMES[lead["best_rid"]],
                summary=lead["result"].get("summary", ""), ta=ta, tb=tb,
                diffs=[d for d in lead["result"]["differences"] if d.get("type") not in ("wording",)])

jobs = sorted({j for _, j in R if (A, j) in R and (B, j) in R})
E = [ensemble(j) for j in jobs]
real = [e for e in E if not e["job"].startswith("ctl")]
print("final tiers (real):", dict(sorted(collections.Counter(e["tier"] for e in real).items())), "review:", sum(e["review"] for e in real))
print("controls broken-ours:", [(e["job"], e["tier"], e["review"]) for e in E if e["job"].startswith("ctl-ours")])
print("planted picked as best:", [e["job"] for e in E if e["best"] == "PLANTED"])
print("judge tier pairs (real):", collections.Counter((e["ta"], e["tb"]) for e in real).most_common())
json.dump(E, open(f"{D}/ensemble.json", "w"), ensure_ascii=False, indent=1)
if "--show" in sys.argv:
    for e in real:
        if e["tier"] >= 1:
            print(f"\n{e['job']} tier={e['tier']}{' REVIEW' if e['review'] else ''} [{e['ta']},{e['tb']}] {e['best']}: {e['summary'][:240]}")
            for d in e["diffs"]:
                print(f"   [{d.get('type')}] '{str(d.get('ours'))[:60]}' -> '{str(d.get('best'))[:60]}'")
