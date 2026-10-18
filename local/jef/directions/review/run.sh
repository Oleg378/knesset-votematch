#!/bin/zsh
cd /Users/oleg/Documents/elections-research
R=jef/directions/review; T=$1
cat $R/$T.md | claude -p --model opus --output-format json --allowedTools "Read($R/*),Write($R/${(L)T}_out.json),Edit($R/${(L)T}_out.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $R/${(L)T}.log 2>&1
echo done
