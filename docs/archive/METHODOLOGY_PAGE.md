# Methodology page — texts shown to the user

_English, as shown on the site. Derived from `docs/METHODOLOGY.md` (concept) and `docs/TECHNICAL.md` (numbers); the data side keeps it current, the web renders it. Numbers marked «from the export» are read from the data files, the rest is fixed text._

**How topics are chosen.** A topic gets a statement only if the parties' former MKs actually differ on it in the Knesset record:
at least 8 evaluated lists with 3 or more former MKs on the topic, a spread of their positions of at least 0.25, and at least 5
distinct bills (a re-submitted bill counts once) sponsored by them. The thresholds were chosen in October 2026 by testing which
values gave positions that held between the 24th and 25th Knesset, and were frozen on 18 October 2026; the same thresholds apply to
every topic, and the full history of the choices is in the project's decision log (open source). Topics where all lists did the same,
or where too few bills exist, are left out — even when they are important. When one topic lies almost entirely inside another, a
shared bill counts toward only one of them, chosen by whether voters would see two different questions.

**Important topics that are not in the quiz, and why** (state as of 22 October 2026).
- *The lists' records hardly differ — nearly everyone pushed the same way:* relief for war and terror victims; support for families
  with children; credit and mortgages (credit for households falls just below the spread threshold); tax enforcement; support for
  charities; public broadcasting (Kan and Army Radio); banning harmful online and broadcast content.
- *Too few lists have a record once budget votes are set aside:* the power of labor unions; defamation law; assisted reproduction.
- *Too few bills by the candidates to place the lists:* abortion; who is registered as a Jew; the Law of Return for grandchildren of
  Jews; gun licensing; immunity for soldiers; laws tied to a state of emergency; the Yemenite children affair; the autonomy of minors;
  cameras in kindergartens and institutions; the term of Supreme Court justices; sports on free channels.
- *Asked by another statement:* selecting judges (in «Politicians' influence over the courts»); the weight of the Attorney General
  (in «Ministers' control over senior officials»); civil marriage and divorce (in «Civil marriage» and «Divorce»); conditions on
  funding religious schools (in «Funding schools without the core curriculum»); alternatives to military service (in «Drafting yeshiva
  students»); international law and UNRWA (in «Foreign states and international organizations in Israel»); the death penalty and
  sanctions on terrorists' families (in «Counter-terrorism measures»); judicial review of government decisions (in «Overriding court
  rulings»); preferences for underrepresented groups (in «Benefits for those who served»); surveillance powers of the security
  services (in «Protection of personal data»); bank fees and duties (in «Protecting the weaker party to a contract»); local preference
  in government purchasing (the mirror of «Imports and competition»).
- *Bills on unrelated subjects, no single honest question:* bans on publishing victims' details; state ownership of disputed property;
  co-owners' rights in apartment buildings; accountability of individual officials; criminal liability of officials for abuse of office.
- *Administrative matters with no position a voter would hold:* licensing procedures for businesses and professions; terms and
  deadlines; the size of public bodies; inheritance law; state awards.
Not present at all, because no bill of a former MK carries the topic in a way that separates the lists: the Gaza war and the
hostages, a Palestinian state, the cost of living as such. The quiz measures legislation, not campaigns.

**Where a list's position comes from.** Only from what its candidates who were MKs in the 24th–25th Knesset did: the bills they
sponsored, their votes on private bills, their votes on the other camp's bills and, for coalition parties, their votes on the government's
own bills. A government bill counts for both camps the same way; votes on the omnibus budget laws count for nobody, because a vote for
or against the whole budget says nothing about its hundred separate articles. Promises and speeches are not used. Sponsoring a bill
counts four times more than a vote on it: the record of a party that pushed for a change is louder than the record of a party that
only voted against it — a deliberate choice, stated here so that it can be judged.

**Whose record a list carries.** A list's record is the record of its candidates who were MKs — for a joint list that can be mostly
the former MKs of one partner. The List details screen says how many former MKs stand behind each list and which parties they came
from. A former MK who moved to another list counts for the list they run with in 2026: it is the same person and their own votes.

**Leaders with few bills of their own.** Ministers and prime ministers rarely sponsor bills, so a list's position rests mostly on
its other former MKs and on votes.

**Lists with one former MK** are shown but not ranked: one person's record is too thin to call a list the closest.

**The order of questions.** The first eight statements are the same for everyone: markers of the main axes along which the lists
differ. The next seven are chosen one at a time to tell apart the lists closest to you so far; a list that fell behind early is not
probed further — «Answer more questions» continues until the pool is exhausted. Which statements are asked also depends on a rating,
made by a language model, of how much a typical voter cares about each topic; it affects only which questions you see, never the
closeness.

**The answer scale.** Closeness compares directions, not intensity: if you answer «strongly agree» to everything, the result is the
same as «agree» to everything; the strength of an answer matters when your answers are mixed. If you answer at random, lists without
a close neighbour (the Arab lists, for example) come first more often than others — the result means something only for considered
answers.

**«No clear position».** A list is marked so when its position is weaker than 0.2 (`params.CLOSE`) — below that, the side of the
same list did not hold between the two Knessets in most cases — or when it rests on a single former MK or a single bill.

**Limitations — what this quiz can and cannot tell you.** The quiz is an orientation, not a precise measurement. We state openly
where the data and the analysis are noisy:
- *Only the Knesset record of former MKs* (24th–25th Knesset) is used. New candidates, platforms and statements are not seen. 12 of
  38 lists can be evaluated; 4 lists with a single former MK are shown but not ranked; 22 lists have no record.
- *Bloc discipline.* About 98 % of votes follow the voter's bloc. A party's votes on the other camp's laws, and a coalition party's
  votes on the government's laws, are partly party discipline, not only conviction; that is why a vote weighs a quarter of a sponsored bill.
- *Leaders and ministers sponsor few bills,* so a list's position rests mostly on its other former MKs and on votes.
- *Topic labels were made by a language model* and corrected by other models: on samples checked blind, main topics were right in
  about 93 % and secondary topics in about 80 % of cases. The systematic checks that followed removed 1 607 labels, added 632 and
  changed 52 signs — each change only where two independent checks agreed; a further 26 522 double counts between nested topics were
  removed. Individual mistakes remain.
- *Checks so far were done by models, not by people.* Agreement figures measure consistency between models, not accuracy for real
  voters; no list's position has yet been confirmed by a person who knows the Knesset.
- *Closeness is approximate.* Lists with close values cannot be told apart reliably, so values are shown rounded and should be read
  as «about as close». «No clear position» means the record is weak or rests on a single former MK or a single bill.
- *The price in a statement* («even if …») is not measured: the record shows what a list's bills and votes pushed for, not whether
  it accepts that price.
- *A vote against a bill can mean the opposite of what the topic sign says* — a party may vote against a draft law because it is too
  lenient, not because it opposes the draft. The method cannot see the reason for a vote.

## Positions of the lists page

Established voting advice applications let parties see and dispute their coded positions before publication. Our equivalent is a
public, complete table of what the quiz holds about every list, built only from data already in the export — no new fields.

**Page «Positions of the lists»** (linked from Methodology and from Results; English):
- Rows: the 123 statements (title_en, grouped by `area` from `statements[]`, in the quiz's area order). Columns: the 12 evaluated
  lists (`status == "ok"`), then the 4 ranked-with-warning lists in a second block; lists without a record are not columns.
- Cell: the list's measured side on the statement — «toward» / «against» / «no clear position» — by the same rule as the
  explanations (`params.CLOSE`, `MIN_CLEAR_MKS`, `MIN_CLEAR_BILLS` on `lists[].positions[d]`); a small marker when the side comes
  from votes only (`P_bills` is 0 or opposite to `P`, as in the «side comes from votes» line). No numbers in the cell.
- Click on a cell → the same bill list as the List details screen for that statement (bills toward / against, votes), so the
  claim is checkable down to the Knesset record.
- Header text (fixed): «This is everything the quiz holds about each list, measured from the bills its candidates who were MKs
  sponsored and how they voted in the 24th–25th Knesset. If you represent a list and believe a cell is wrong, the bills behind
  it are listed — open an issue at https://github.com/Oleg378/knesset-votematch/issues with the bill and the reason; corrections
  are published here.» (customer, 2026-10-22: contact = GitHub issues).
- Export: `quiz_data.json` + `quiz_bills.json` only; the page is static like the rest.

**Composition of the list's record** (external audit №3, п. 1.4; data exported 2026-10-22, how to display is the customer's
separate decision): `mks[].party_en` — the component party of the 2026 list the former MK runs with (Central Elections Committee
candidate list; English names `manual/party_names_en.csv`; null = the list itself), and `lists[].composition` — the same
aggregated: `[{"party_en": "Yesh Atid", "ex_mks": 17}, {"party_en": "Be’Yahad (Bennett)", "ex_mks": 2}]`, most first. Proposed
line on the List details screen, under the header: «Based on 19 former MKs: 17 from Yesh Atid, 2 from Be’Yahad». The methodology
text (section 6, «Whose record a list carries») already refers to it.
