# Data: knesset.duckdb and raw/ are not in git (rebuilt by pipeline/fetch/ and pipeline/build/build.py, Israeli IP needed).
.PHONY: data positions export test web-dev web-build snapshot-save snapshot-restore

check:                    ## invariants of the quiz data (run after every stage and before release)
	python3 pipeline/check_invariants.py

data: positions export          ## positions -> export/quiz_{core,data,bills}.json + golden.json

positions:
	python3 pipeline/positions.py

export:
	python3 pipeline/export.py

test:                           ## web tests incl. golden cases (TS port == Python reference)
	cd web && npm test -- --run

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

snapshot-save:                  ## the database and raw inputs -> private repo Oleg378/knesset-votematch-data (pipeline/snapshot.py)
	python3 pipeline/snapshot.py save

snapshot-restore:               ## fetch them back (a fresh machine or CI): then make data / make check work
	python3 pipeline/snapshot.py restore
