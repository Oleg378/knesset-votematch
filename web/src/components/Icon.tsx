import back from '../assets/figma/icon-back.svg';
import behance from '../assets/figma/icon-behance.svg';
import close from '../assets/figma/close.svg';
import equalDefault from '../assets/figma/equal-default.svg';
import equalSelected from '../assets/figma/equal-selected.svg';
import github from '../assets/figma/icon-github.svg';
// Not in Figma: the menu's Home, drawn in the Figma icons' style (2 px blue stroke, round ends; customer 2026-10-25)
import home from '../assets/icon-home.svg';
import info from '../assets/figma/icon-info.svg';
import menu from '../assets/figma/menu.svg';
import restart from '../assets/figma/icon-restart.svg';
import results from '../assets/figma/icon-results.svg';

/** Figma icons (downloaded as-is into src/assets/figma), and Home. Decorative: the control around them carries the label. */
const ICONS = { back, behance, close, equalDefault, equalSelected, github, home, info, menu, restart, results };

export function Icon({ name, size = 24 }: { name: keyof typeof ICONS; size?: number }) {
  return <img src={ICONS[name]} alt="" width={size} height={name.startsWith('equal') ? (size * 8) / 12 : size} />;
}
