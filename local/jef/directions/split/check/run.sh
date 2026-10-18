#!/bin/zsh
cd /Users/oleg/Documents/elections-research
T=jef/directions/split/check
cat $T/REVIEW.md | claude -p --model opus --output-format json --allowedTools "Read($T/input.json),Write($T/out.json),Edit($T/out.json),Read($T/out.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $T/log.json 2>&1
echo done
