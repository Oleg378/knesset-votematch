#!/bin/zsh
# usage: run.sh K [model]   — with a model: --model MODEL, output batch_K.MODEL.out.json, log batch_K.MODEL.log
cd /Users/oleg/Documents/elections-research
B=jef/directions/blind; K=$1; M=$2
S=${M:+.$M}
sed "s/batch_0\.out\.json/batch_$K$S.out.json/; s/batch_0/batch_$K/g" $B/DISCOVER.md | claude -p ${=M:+--model $M} --output-format json --allowedTools "Read($B/batch_$K.jsonl),Edit($B/batch_$K$S.out.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > jef/directions/batch_$K$S.log 2>&1
echo done $K $M
