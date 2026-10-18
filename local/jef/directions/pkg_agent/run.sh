#!/bin/zsh
# usage: run.sh NN  — label batch NN with Opus (blind, no tools except reading inputs and writing the output)
cd /Users/oleg/Documents/elections-research
T=jef/directions/pkg_agent; K=$1
sed "s/batch_NN/batch_$K/; s/out_NN/out_$K/; s/(NN — номер пачки)//" $T/LABEL.md | claude -p --model opus --output-format json --allowedTools "Read($T/directions.tsv),Read($T/batch_$K.json),Write($T/out_$K.json),Edit($T/out_$K.json),Read($T/out_$K.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $T/log_$K.json 2>&1
python3 - $K <<'PY'
import json,sys
k=sys.argv[1]; T="jef/directions/pkg_agent"
ids={x["vote_id"] for x in json.load(open(f"{T}/batch_{k}.json"))}
o=json.load(open(f"{T}/out_{k}.json")); got={str(v["vote_id"]) for v in o["votes"]}
dirs={l.split("\t")[0] for l in open(f"{T}/directions.tsv")}
bad=[m["n"] for v in o["votes"] for m in v["main"]+v["secondary"] if str(m["n"]) not in dirs]
cost=json.load(open(f"{T}/log_{k}.json")).get("total_cost_usd")
print(f"batch {k}: {len(got&ids)}/{len(ids)} votes, missing {sorted(ids-got)}, unknown n {bad}, cost {cost}")
sys.exit(0 if ids<=got and not bad else 1)
PY
