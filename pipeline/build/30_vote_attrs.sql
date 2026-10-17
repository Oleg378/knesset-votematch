-- Per-vote attributes computed from MK-level results.
-- Bloc = voting bloc from manual/coalition.csv (not strictly government membership); see docs/SHARED_UNDERSTANDING.md (B2).
-- bloc 'none' = outside blocs (interregnum, unaligned factions): never compared against a bloc line. Faction level only: party_2026 mapping comes later (manual).

-- Everyone who was an MK on the vote date, with their faction and bloc; result NULL = absent.
CREATE TABLE vote_roster AS
WITH roster AS (
    SELECT DISTINCT v.vote_id, v.vote_date, t.mk_id
    FROM votes v JOIN mk_terms t ON v.vote_date >= t.date_from AND v.vote_date < t.date_to
), present AS (
    SELECT r.vote_id, v.vote_date, r.mk_id, r.faction_id, r.result
    FROM vote_results r JOIN votes v USING (vote_id)
), absent AS (
    SELECT ro.vote_id, ro.vote_date, ro.mk_id,
           (SELECT m.faction_id FROM faction_membership m
            WHERE m.mk_id = ro.mk_id AND ro.vote_date BETWEEN m.date_from AND m.date_to
            ORDER BY m.date_from DESC LIMIT 1) AS faction_id,
           NULL AS result
    FROM roster ro ANTI JOIN present p USING (vote_id, mk_id)
), alln AS (SELECT * FROM present UNION ALL SELECT * FROM absent)
SELECT a.vote_id, a.mk_id, a.faction_id, a.result,
       (SELECT c.bloc FROM coalition c
        WHERE c.faction_id = a.faction_id AND a.vote_date BETWEEN c.date_from AND c.date_to
        ORDER BY c.date_from DESC LIMIT 1) AS bloc
FROM alln a;


CREATE TABLE faction_vote AS
SELECT vote_id, faction_id, any_value(bloc) AS bloc,
       count(*) AS n_members,
       count(*) FILTER (result = 'for') AS n_for,
       count(*) FILTER (result = 'against') AS n_against,
       count(*) FILTER (result = 'abstain') AS n_abstain,
       count(result) AS n_present,
       count(result) / count(*) AS participation,
       CASE WHEN count(*) FILTER (result IN ('for','against')) > 0
            THEN count(*) FILTER (result = 'for') / count(*) FILTER (result IN ('for','against')) END AS p_for
FROM vote_roster GROUP BY ALL;

CREATE TABLE bloc_vote AS
SELECT vote_id, coalesce(bloc, 'unknown') AS bloc,
       count(*) AS n_members,
       count(*) FILTER (result = 'for') AS n_for,
       count(*) FILTER (result = 'against') AS n_against,
       count(result) AS n_present,
       count(result) / count(*) AS participation,
       CASE WHEN count(*) FILTER (result IN ('for','against')) > 0
            THEN greatest(count(*) FILTER (result = 'for'), count(*) FILTER (result = 'against'))
                 / count(*) FILTER (result IN ('for','against')) END AS cohesion,
       CASE WHEN count(*) FILTER (result = 'for') > count(*) FILTER (result = 'against') THEN 'for'
            WHEN count(*) FILTER (result = 'for') < count(*) FILTER (result = 'against') THEN 'against' END AS direction
FROM vote_roster GROUP BY ALL;

CREATE TABLE vote_attrs AS
WITH tot AS (
    SELECT vote_id,
           count(*) FILTER (result = 'for') AS n_for,
           count(*) FILTER (result = 'against') AS n_against,
           count(*) FILTER (result = 'abstain') AS n_abstain,
           count(result) AS n_present,
           count(*) AS n_roster,
           count(*) FILTER (result NOT IN ('for','against','abstain','present_not_voting')) AS n_nonstandard
    FROM vote_roster GROUP BY 1
), b AS (
    SELECT vote_id,
           any_value(direction) FILTER (bloc = 'coalition') AS coal_dir,
           any_value(cohesion) FILTER (bloc = 'coalition') AS coal_cohesion,
           any_value(participation) FILTER (bloc = 'coalition') AS coal_participation,
           any_value(n_for + n_against) FILTER (bloc = 'coalition') AS coal_voters,
           any_value(direction) FILTER (bloc = 'opposition') AS opp_dir,
           any_value(cohesion) FILTER (bloc = 'opposition') AS opp_cohesion,
           any_value(participation) FILTER (bloc = 'opposition') AS opp_participation,
           any_value(n_for + n_against) FILTER (bloc = 'opposition') AS opp_voters
    FROM bloc_vote GROUP BY 1
), dissent AS (  -- factions (>=2 voters) whose majority went against their own bloc's majority
    SELECT f.vote_id, list(fa.name ORDER BY fa.name) AS dissenting_factions
    FROM faction_vote f JOIN bloc_vote bv USING (vote_id, bloc) JOIN factions fa USING (faction_id)
    WHERE f.bloc IN ('coalition', 'opposition') AND f.n_for + f.n_against >= 2 AND f.p_for <> 0.5 AND bv.direction IS NOT NULL
      AND (CASE WHEN f.p_for > 0.5 THEN 'for' ELSE 'against' END) <> bv.direction
    GROUP BY 1
), pivots AS (  -- factions whose switch alone would flip the outcome
    SELECT f.vote_id, list(fa.name ORDER BY fa.name) AS pivotal_factions
    FROM faction_vote f JOIN tot t USING (vote_id) JOIN factions fa USING (faction_id)
    WHERE (t.n_for <= t.n_against AND 2 * f.n_against > t.n_against - t.n_for AND f.n_against > 0)
       OR (t.n_for > t.n_against AND 2 * f.n_for > t.n_for - t.n_against AND f.n_for > 0)
    GROUP BY 1
)
SELECT v.vote_id, v.vote_date, v.knesset, v.bill_id, v.stage, v.for_option_id,
       CASE
           WHEN v.method NOT IN ('אלקטרונית', 'שמית') OR t.n_nonstandard > 0 THEN 'no_rollcall'
           WHEN v.title LIKE '%התפזרות הכנסת%' OR v.title LIKE '%פיזור הכנסת%' THEN 'procedural_power'
           WHEN v.is_no_confidence OR v.for_option_id = 16 THEN 'no_confidence'
           WHEN v.for_option_id = 7 THEN 'reservation'
           WHEN v.stage IS NOT NULL THEN 'bill'
           WHEN v.for_option_id IN (14, 17, 18, 19, 20) THEN 'agenda_motion'
           WHEN v.for_option_id = 23 THEN 'secondary_legislation'
           ELSE 'procedural'
       END AS kind,
       v.title LIKE 'הצעת חוק-יסוד%' OR v.title LIKE 'חוק-יסוד%' AS is_basic_law,
       t.n_for, t.n_against, t.n_abstain, t.n_present, t.n_roster,
       t.n_for > t.n_against AS accepted,
       CASE
           WHEN least(coalesce(b.coal_participation, 0), coalesce(b.opp_participation, 0)) < 0.1
            AND greatest(coalesce(b.coal_participation, 0), coalesce(b.opp_participation, 0)) >= 0.4 THEN 'one_bloc_absent'
           WHEN t.n_present < 25 THEN 'low_turnout'
           ELSE 'normal'
       END AS participation_pattern,
       CASE
           WHEN b.coal_voters IS NULL AND b.opp_voters IS NULL THEN 'no_blocs'
           WHEN coalesce(b.coal_voters, 0) < 3 OR coalesce(b.opp_voters, 0) < 3 THEN 'one_bloc_only'
           WHEN b.coal_dir = b.opp_dir AND b.coal_cohesion >= 0.9 AND b.opp_cohesion >= 0.9 THEN 'consensus'
           WHEN b.coal_dir = b.opp_dir THEN 'cross_bloc_majority'   -- both blocs agree, a minority dissents (e.g. UNRWA)
           WHEN b.coal_cohesion >= 0.9 AND b.opp_cohesion >= 0.9 THEN 'bloc_line'
           ELSE 'bloc_line_with_dissent'                           -- blocs opposed, some faction(s) broke ranks
       END AS split_pattern,
       b.coal_dir, round(b.coal_cohesion, 2) AS coal_cohesion, round(b.coal_participation, 2) AS coal_participation,
       b.opp_dir, round(b.opp_cohesion, 2) AS opp_cohesion, round(b.opp_participation, 2) AS opp_participation,
       d.dissenting_factions, p.pivotal_factions,
       v.title, v.subject, v.for_option
FROM votes v
JOIN tot t USING (vote_id)
LEFT JOIN b USING (vote_id)
LEFT JOIN dissent d USING (vote_id)
LEFT JOIN pivots p USING (vote_id);
