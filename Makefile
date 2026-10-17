# Data: knesset.duckdb and data/ are not in git (rebuilt by pipeline/fetch_* and pipeline/build/build.py, Israeli IP needed).
.PHONY: data positions export test web-dev web-build

data: positions export          ## positions -> export/quiz_{core,data,bills}.v2.json + golden.v2.json

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
