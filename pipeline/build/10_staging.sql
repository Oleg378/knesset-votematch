-- Normalized tables from raw OData dumps. One row per real-world entity; no derived metrics here.
-- Timestamps are read as strings: DuckDB auto-detect converts '+03:00' to UTC and shifts
-- votes after midnight Israel time to the previous day. d() takes the local (Israel) date.
CREATE MACRO d(s) AS CASE WHEN s IS NULL OR s LIKE '0001-%' THEN NULL ELSE substr(s, 1, 10)::DATE END;

CREATE TABLE knesset_terms AS
SELECT KnessetNum AS knesset, min(d(PlenumStart)) AS date_from,
       coalesce(max(d(PlenumFinish)), DATE '9999-12-31') AS last_session_end
FROM read_json_auto('data/knesset_dates.json', timestampformat = 'none', dateformat = 'none') GROUP BY 1;

CREATE TABLE factions AS
SELECT Id AS faction_id, KnessetNum AS knesset, trim(Name) AS name,
       d(StartDate) AS date_from, coalesce(d(FinishDate), DATE '9999-12-31') AS date_to
FROM read_json_auto('data/faction_24_25.json', timestampformat = 'none', dateformat = 'none');

-- Faction membership intervals (PositionID 54 member, 48 chair).
CREATE TABLE faction_membership AS
SELECT DISTINCT PersonID AS mk_id, FactionID AS faction_id, KnessetNum AS knesset,
       d(StartDate) AS date_from, coalesce(d(FinishDate), DATE '9999-12-31') AS date_to
FROM read_json_auto('data/person_to_position_24_25.json', timestampformat = 'none', dateformat = 'none')
WHERE PositionID IN (54, 48) AND FactionID IS NOT NULL;

-- Knesset membership intervals (PositionID 43 / 61: MK). Used to detect absence.
CREATE TABLE mk_terms AS
SELECT DISTINCT PersonID AS mk_id, KnessetNum AS knesset,
       d(StartDate) AS date_from, coalesce(d(FinishDate), DATE '9999-12-31') AS date_to
FROM read_json_auto('data/person_to_position_24_25.json', timestampformat = 'none', dateformat = 'none')
WHERE PositionID IN (43, 61);

CREATE TABLE statuses AS
SELECT Id AS status_id, "Desc" AS status, TypeDesc AS status_type FROM read_json_auto('data/status.json', timestampformat = 'none', dateformat = 'none');

CREATE TABLE bills AS
SELECT Id AS bill_id, KnessetNum AS knesset, trim(Name) AS name, SubTypeDesc AS bill_type,
       PrivateNumber AS private_number, CommitteeID AS committee_id, StatusID AS status_id,
       IsContinuationBill AS is_continuation, SummaryLaw AS summary,
       PostponementReasonDesc AS postponement_reason
FROM read_json_auto('data/bills/bill.json', timestampformat = 'none', dateformat = 'none');

CREATE TABLE bill_initiators AS
SELECT BillID AS bill_id, PersonID AS mk_id, IsInitiator AS is_initiator, Ordinal AS ordinal
FROM read_json_auto('data/bills/bill_initiator.json', timestampformat = 'none', dateformat = 'none')
WHERE BillID IN (SELECT bill_id FROM bills);

CREATE TABLE bill_initiator_history AS
SELECT BillID AS bill_id, PersonID AS mk_id, IsInitiator AS is_initiator,
       d(EndDate) AS date_to, ReasonDesc AS reason
FROM read_json_auto('data/bills/bill_history_initiator.json', timestampformat = 'none', dateformat = 'none')
WHERE BillID IN (SELECT bill_id FROM bills);

CREATE TABLE committee_bill_sessions AS
SELECT i.ItemID AS bill_id, s.CommitteeID AS committee_id, s.Id AS session_id, d(s.StartDate) AS session_date
FROM read_json_auto('data/bills/cmt_session_item.json', timestampformat = 'none', dateformat = 'none') i
JOIN read_json_auto('data/bills/committee_session.json', timestampformat = 'none', dateformat = 'none') s ON s.Id = i.CommitteeSessionID
WHERE i.ItemTypeID = 2;

-- The server returns some votes as several identical rows (e.g. Id 44998 x4), hence DISTINCT.
CREATE TABLE votes AS
SELECT DISTINCT Id AS vote_id,
       d(VoteDateTime) AS vote_date,
       VoteDateTime::TIMESTAMPTZ AS vote_ts,
       CASE WHEN d(VoteDateTime) >= DATE '2022-11-15' THEN 25 ELSE 24 END AS knesset,
       ItemID AS item_id,
       CASE WHEN stage IS NOT NULL THEN ItemID END AS bill_id,
       stage, ForOptionID AS for_option_id, ForOptionDesc AS for_option,
       VoteMethodDesc AS method, VoteTitle AS title, VoteSubject AS subject,
       coalesce(IsNoConfidenceInGov, false) AS is_no_confidence
FROM read_json_auto('data/export/votes.json', timestampformat = 'none', dateformat = 'none');

-- Per-MK results. Fill the few rows without faction (Norwegian-law returns) with the nearest membership interval.
CREATE TABLE vote_results AS
WITH r AS (SELECT * FROM read_json_auto('data/export/vote_results.json', timestampformat = 'none', dateformat = 'none'))
SELECT r.vote_id, r.mk_id, r.name,
       coalesce(r.faction_id, (
           SELECT m.faction_id FROM faction_membership m
           WHERE m.mk_id = r.mk_id
           ORDER BY least(abs(date_diff('day', m.date_from, v.vote_date)), abs(date_diff('day', m.date_to, v.vote_date)))
           LIMIT 1)) AS faction_id,
       r.result
FROM r JOIN votes v USING (vote_id);

CREATE TABLE coalition AS
SELECT faction_id, date_from::DATE AS date_from, coalesce(date_to::DATE, DATE '9999-12-31') AS date_to, bloc, source, note
FROM read_csv('manual/coalition.csv', header = true, all_varchar = true)
WHERE bloc IS NOT NULL AND bloc <> '';
