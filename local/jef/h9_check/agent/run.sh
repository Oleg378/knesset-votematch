#!/bin/zsh
cd /Users/oleg/Documents/elections-research
T=jef/h9_check/agent; K=$1
sed "s/input_K/input_$K/; s/out_K/out_$K/" $T/REVIEW.md | claude -p --model opus --output-format json --allowedTools "Read($T/directions.tsv),Read($T/input_$K.json),Write($T/out_$K.json),Edit($T/out_$K.json),Read($T/out_$K.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $T/log_$K.json 2>&1
echo done $K
