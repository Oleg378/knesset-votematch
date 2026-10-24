/** How many of the closest lists stand out on the Results scale (customer 2026-10-22); the start page names the number. */
export const HIGHLIGHT = 5;

/**
 * How it works: a card collapses by its height, one rule for every card, so the collapsed cards come out about the
 * same height (customer 2026-10-24: «все темы сворачиваются, если их длина больше чем сколько-то», then «по высоте»,
 * a count of items gave a «какофония»). The card's content — its title with the text and its items (the bullets of a
 * section, its closing paragraph the last item; the names of a lists card; the rows of the statements card) — measured
 * in the browser at the current width: up to CARD_MAX_HEIGHT px it is all shown; above, the title, the text and as many
 * whole items as fit in CARD_MAX_HEIGHT together with «See all» (at least one), the rest drop down (MethodCard).
 */
export const CARD_MAX_HEIGHT = 360;
