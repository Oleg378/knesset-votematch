#!/bin/zsh
# Blind two-pass markup by agent $1 (A|B): only its own folder and the shared input are accessible.
cd /Users/oleg/Documents/elections-research
B=jef/pilot_changes/blind; X=$1
claude -p --allowedTools "Read($B/input.jsonl),Edit($B/$X/pass1.jsonl)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" < $B/$X/PASS1.md > jef/pilot_changes/$X.pass1.log 2>&1
claude -p --allowedTools "Read($B/$X/pass1.jsonl),Edit($B/$X/pass2.json)" --disallowedTools "Bash,WebFetch,WebSearch,Agent,Glob,Grep" < $B/$X/PASS2.md > jef/pilot_changes/$X.pass2.log 2>&1
echo done $X
