# Sensitivity of the pool and the core to the thresholds (2026-10-18)

Current rule: lists >= 8, SD >= 0.25, volume (pairs) >= 25. Pool now: 78 statements.

## Distinct bills vs pairs for the current statements

| q | title | pairs | distinct bills |
|---|---|---|---|
| q104 | Term of Supreme Court justices | 46 | 10 |
| q64 | A prime minister under indictment | 29 | 10 |
| q59 | Guardianship of violent parents | 40 | 11 |
| q105 | Checks on the prime minister's power | 35 | 11 |
| q19 | Funding schools without the core curriculum | 40 | 12 |
| q72 | Land purchase in Judea and Samaria | 71 | 12 |
| q98 | Tax enforcement | 29 | 13 |
| q7 | Drafting yeshiva students | 62 | 14 |
| q5 | Community heritage centers | 56 | 16 |
| q8 | Compulsory service for everyone | 52 | 17 |
| q41 | Autonomy of minors | 36 | 17 |
| q70 | Religious rules in public institutions | 86 | 17 |
| q81 | Dismissing employees who support terror | 50 | 18 |
| q22 | Civil marriage | 53 | 18 |
| q23 | Public sector wages | 56 | 19 |
| q25 | Separate spaces for men and women | 49 | 19 |
| q18 | Prison conditions for terrorism convicts | 67 | 20 |
| q103 | Prime minister term limits | 51 | 20 |
| q16 | Assisted reproduction | 47 | 21 |
| q21 | Foreign government funding of non-profits | 40 | 21 |
| q36 | Settlements | 58 | 22 |
| q83 | Withholding Palestinian Authority funds | 60 | 23 |
| q71 | Wartime relief | 42 | 23 |
| q6 | Revoking citizenship for terrorism | 102 | 23 |
| q39 | Defamation laws | 66 | 25 |
| q20 | Divorce | 71 | 25 |
| q48 | Vetting senior appointments | 33 | 26 |
| q14 | Foreign workers: quotas | 63 | 26 |
| q13 | Foreign states and international organizations in Israel | 118 | 27 |
| q1 | Selecting judges | 50 | 27 |
| q35 | Public transport funding | 62 | 28 |
| q60 | Confiscation of property without conviction | 62 | 28 |
| q38 | Early withdrawal of long-term savings | 41 | 29 |
| q100 | Pensions for seniors and survivors | 68 | 31 |
| q51 | Help for new immigrants | 81 | 32 |
| q99 | Monitoring of violent partners | 57 | 32 |
| q82 | Access to higher education | 70 | 34 |
| q86 | Support for farmers | 87 | 34 |
| q12 | Rights of foreign workers and asylum seekers | 51 | 35 |
| q101 | Free public education | 84 | 36 |
| q61 | Weight of the Attorney General | 95 | 37 |
| q4 | Jewish character of the state | 77 | 39 |
| q78 | Support for students | 94 | 41 |
| q3 | Trade with hostile countries | 149 | 44 |
| q88 | Access to voting | 108 | 45 |
| q69 | Minimum sentences | 85 | 47 |
| q24 | Politicians' influence over the courts | 89 | 49 |
| q52 | Protecting the weaker party to a contract | 129 | 50 |
| q68 | Rights of ordinary prisoners | 109 | 52 |
| q66 | Conditions on child benefits | 121 | 53 |
| q63 | Overriding court rulings | 140 | 55 |
| q85 | Survivors' benefits | 131 | 56 |
| q77 | Unemployment benefits | 98 | 57 |
| q54 | Denying benefits for terrorism | 131 | 58 |
| q74 | Equality in the Basic Laws | 171 | 64 |
| q75 | Women's representation | 180 | 68 |
| q37 | Housing construction | 147 | 69 |
| q53 | Privatization of public services | 105 | 71 |
| q92 | Disability and sickness benefits | 140 | 74 |
| q10 | Entry of foreigners | 254 | 77 |
| q2 | Sovereignty in Judea and Samaria | 202 | 86 |
| q33 | Rabbinical courts in civil disputes | 164 | 88 |
| q94 | Local tax discounts | 285 | 95 |
| q90 | Powers of municipalities | 234 | 97 |
| q40 | LGBT rights | 233 | 103 |
| q49 | Rights of suspects | 209 | 109 |
| q62 | Ministers' control over senior officials | 229 | 110 |
| q89 | Health fund services | 216 | 113 |
| q96 | Oversight of security forces | 321 | 131 |
| q93 | Environmental regulation | 384 | 135 |
| q47 | Police powers | 336 | 139 |
| q95 | Protection of debtors | 249 | 141 |
| q80 | Challenging the authorities | 323 | 149 |
| q45 | Counter-terrorism measures | 451 | 150 |
| q42 | Imports and competition | 416 | 180 |
| q55 | Protection of personal data | 423 | 189 |
| q9 | Benefits for those who served | 831 | 252 |
| q15 | Payments to reservists and veterans | 1390 | 418 |

## Pool by thresholds

Dropped = current statements that would fail; New = directions without a statement that would pass (would need the usual flow).

| volume | SD | pool (current statements kept) | dropped | new candidates |
|---|---|---|---|---|
| pairs ≥ 20 | ≥ 0.20 | 78 | 0:  | 103 |
| pairs ≥ 20 | ≥ 0.25 | 78 | 0:  | 72 |
| pairs ≥ 20 | ≥ 0.30 | 66 | 12: Separate spaces for men and women, Wartime relief, Access to voting, Powers of municipalities, Environmental regulation, Local tax discounts, Protection of debtors, Oversight of security forces, Tax enforcement, Monitoring of violent partners, Pensions for seniors and survivors, Free public education | 43 |
| pairs ≥ 25 | ≥ 0.20 | 78 | 0:  | 91 |
| pairs ≥ 25 | ≥ 0.25 | 78 | 0:  | 62 |
| pairs ≥ 25 | ≥ 0.30 | 66 | 12: Separate spaces for men and women, Wartime relief, Access to voting, Powers of municipalities, Environmental regulation, Local tax discounts, Protection of debtors, Oversight of security forces, Tax enforcement, Monitoring of violent partners, Pensions for seniors and survivors, Free public education | 35 |
| pairs ≥ 30 | ≥ 0.20 | 76 | 2: A prime minister under indictment, Tax enforcement | 85 |
| pairs ≥ 30 | ≥ 0.25 | 76 | 2: A prime minister under indictment, Tax enforcement | 57 |
| pairs ≥ 30 | ≥ 0.30 | 65 | 13: Separate spaces for men and women, A prime minister under indictment, Wartime relief, Access to voting, Powers of municipalities, Environmental regulation, Local tax discounts, Protection of debtors, Oversight of security forces, Tax enforcement, Monitoring of violent partners, Pensions for seniors and survivors … | 32 |
| bills ≥ 8 | ≥ 0.20 | 78 | 0:  | 109 |
| bills ≥ 8 | ≥ 0.25 | 78 | 0:  | 77 |
| bills ≥ 8 | ≥ 0.30 | 66 | 12: Separate spaces for men and women, Wartime relief, Access to voting, Powers of municipalities, Environmental regulation, Local tax discounts, Protection of debtors, Oversight of security forces, Tax enforcement, Monitoring of violent partners, Pensions for seniors and survivors, Free public education | 43 |
| bills ≥ 10 | ≥ 0.20 | 78 | 0:  | 104 |
| bills ≥ 10 | ≥ 0.25 | 78 | 0:  | 73 |
| bills ≥ 10 | ≥ 0.30 | 66 | 12: Separate spaces for men and women, Wartime relief, Access to voting, Powers of municipalities, Environmental regulation, Local tax discounts, Protection of debtors, Oversight of security forces, Tax enforcement, Monitoring of violent partners, Pensions for seniors and survivors, Free public education | 40 |
| bills ≥ 12 | ≥ 0.20 | 74 | 4: Guardianship of violent parents, A prime minister under indictment, Term of Supreme Court justices, Checks on the prime minister's power | 97 |
| bills ≥ 12 | ≥ 0.25 | 74 | 4: Guardianship of violent parents, A prime minister under indictment, Term of Supreme Court justices, Checks on the prime minister's power | 66 |
| bills ≥ 12 | ≥ 0.30 | 62 | 16: Separate spaces for men and women, Guardianship of violent parents, A prime minister under indictment, Wartime relief, Access to voting, Powers of municipalities, Environmental regulation, Local tax discounts, Protection of debtors, Oversight of security forces, Tax enforcement, Monitoring of violent partners … | 36 |
| bills ≥ 15 | ≥ 0.20 | 70 | 8: Drafting yeshiva students, Funding schools without the core curriculum, Guardianship of violent parents, A prime minister under indictment, Land purchase in Judea and Samaria, Tax enforcement, Term of Supreme Court justices, Checks on the prime minister's power | 85 |
| bills ≥ 15 | ≥ 0.25 | 70 | 8: Drafting yeshiva students, Funding schools without the core curriculum, Guardianship of violent parents, A prime minister under indictment, Land purchase in Judea and Samaria, Tax enforcement, Term of Supreme Court justices, Checks on the prime minister's power | 57 |
| bills ≥ 15 | ≥ 0.30 | 59 | 19: Drafting yeshiva students, Funding schools without the core curriculum, Separate spaces for men and women, Guardianship of violent parents, A prime minister under indictment, Wartime relief, Land purchase in Judea and Samaria, Access to voting, Powers of municipalities, Environmental regulation, Local tax discounts, Protection of debtors … | 30 |
| bills ≥ 20 | ≥ 0.20 | 62 | 16: Community heritage centers, Drafting yeshiva students, Compulsory service for everyone, Funding schools without the core curriculum, Civil marriage, Public sector wages, Separate spaces for men and women, Autonomy of minors, Guardianship of violent parents, A prime minister under indictment, Religious rules in public institutions, Land purchase in Judea and Samaria … | 79 |
| bills ≥ 20 | ≥ 0.25 | 62 | 16: Community heritage centers, Drafting yeshiva students, Compulsory service for everyone, Funding schools without the core curriculum, Civil marriage, Public sector wages, Separate spaces for men and women, Autonomy of minors, Guardianship of violent parents, A prime minister under indictment, Religious rules in public institutions, Land purchase in Judea and Samaria … | 53 |
| bills ≥ 20 | ≥ 0.30 | 52 | 26: Community heritage centers, Drafting yeshiva students, Compulsory service for everyone, Funding schools without the core curriculum, Civil marriage, Public sector wages, Separate spaces for men and women, Autonomy of minors, Guardianship of violent parents, A prime minister under indictment, Religious rules in public institutions, Wartime relief … | 30 |

## Core by the similarity limit (current pool)

- r_max 0.6: Entry of foreigners · Foreign workers: quotas · Drafting yeshiva students · Compulsory service for everyone · Rights of suspects · Public sector wages · Imports and competition · Prime minister term limits
- r_max 0.7: Entry of foreigners · A prime minister under indictment · Trade with hostile countries · Foreign workers: quotas · Drafting yeshiva students · Civil marriage · Rights of suspects · Weight of the Attorney General
- r_max 0.8: Entry of foreigners · A prime minister under indictment · Trade with hostile countries · Foreign workers: quotas · Selecting judges · Drafting yeshiva students · Overriding court rulings · LGBT rights
