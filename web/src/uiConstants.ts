/** How many of the closest lists stand out on the Results scale (customer 2026-10-22); the start page names the number. */
export const HIGHLIGHT = 5;

/**
 * How it works: a card collapses by its length, one rule for every card (customer 2026-10-24: «все темы
 * сворачиваются, если их длина больше чем сколько-то»). Items: the bullets of a section (its closing paragraph is the
 * last item), the names of a lists card, the rows of the statements card. More than CARD_COLLAPSE_OVER items — the
 * title, the text and the first CARD_PREVIEW items are shown, the rest drop down with «See all»; otherwise all.
 */
export const CARD_PREVIEW = 3;
export const CARD_COLLAPSE_OVER = 4;
