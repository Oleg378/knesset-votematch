#!/bin/zsh
cd /Users/oleg/Documents/elections-research
T=jef/directions/jev_test3
cat $T/REVIEW.md | claude -p --model opus --output-format json --allowedTools "Read($T/directions.tsv),Read($T/review_input.json),Write($T/review_out.json),Edit($T/review_out.json),Read($T/review_out.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" > $T/review.log 2>&1
echo done
