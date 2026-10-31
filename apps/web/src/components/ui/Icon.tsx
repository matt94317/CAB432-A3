import alertIcon from "@/assets/icons/circle-alert.svg";
import arrowRight from "@/assets/icons/arrow-right.svg";
import arrowUpRight from "@/assets/icons/arrow-up-right.svg";
import calendar from "@/assets/icons/calendar.svg";
import calendarClock from "@/assets/icons/calendar-clock.svg";
import chartNoAxes from "@/assets/icons/chart-no-axes-combined.svg";
import checkIcon from "@/assets/icons/circle-check.svg";
import chevronDown from "@/assets/icons/chevron-down.svg";
import chevronRight from "@/assets/icons/chevron-right.svg";
import chevronsUpDown from "@/assets/icons/chevrons-up-down.svg";
import clapperboard from "@/assets/icons/clapperboard.svg";
import download from "@/assets/icons/download.svg";
import ellipsis from "@/assets/icons/ellipsis.svg";
import externalLink from "@/assets/icons/external-link.svg";
import eye from "@/assets/icons/eye.svg";
import eyeOff from "@/assets/icons/eye-off.svg";
import heart from "@/assets/icons/heart.svg";
import heartHandshake from "@/assets/icons/heart-handshake.svg";
import instagram from "@/assets/icons/instagram.svg";
import layoutDashboard from "@/assets/icons/layout-dashboard.svg";
import linkedin from "@/assets/icons/linkedin.svg";
import megaphone from "@/assets/icons/megaphone.svg";
import minus from "@/assets/icons/minus.svg";
import music from "@/assets/icons/music-2.svg";
import play from "@/assets/icons/play.svg";
import plus from "@/assets/icons/plus.svg";
import refresh from "@/assets/icons/refresh-cw.svg";
import search from "@/assets/icons/search.svg";
import send from "@/assets/icons/send.svg";
import sparkles from "@/assets/icons/sparkles.svg";
import tick from "@/assets/icons/check.svg";
import trendingUp from "@/assets/icons/trending-up.svg";
import users from "@/assets/icons/users.svg";
import usersRound from "@/assets/icons/users-round.svg";
import video from "@/assets/icons/video.svg";
import close from "@/assets/icons/x.svg";
import youtube from "@/assets/icons/youtube.svg";

// Icons exported from the Hookd Figma file (Lucide set). They're drawn as a CSS mask, so
// they take the current text colour: `<Icon name="users" className="size-4 text-brand" />`.
const ICONS = {
  alert: alertIcon,
  "arrow-right": arrowRight,
  "arrow-up-right": arrowUpRight,
  calendar,
  "calendar-clock": calendarClock,
  check: checkIcon,
  "chevron-down": chevronDown,
  "chevron-right": chevronRight,
  "chevrons-up-down": chevronsUpDown,
  chart: chartNoAxes,
  clapperboard,
  close,
  download,
  ellipsis,
  "external-link": externalLink,
  eye,
  "eye-off": eyeOff,
  heart,
  "heart-handshake": heartHandshake,
  instagram,
  "layout-dashboard": layoutDashboard,
  linkedin,
  megaphone,
  minus,
  music,
  play,
  plus,
  refresh,
  search,
  send,
  sparkles,
  "trending-up": trendingUp,
  tick,
  users,
  "users-round": usersRound,
  video,
  youtube,
};

export type IconName = keyof typeof ICONS;

export default function Icon({ name, className = "size-4" }: { name: IconName; className?: string }) {
  const url = `url("${ICONS[name]}")`;
  return (
    <span
      aria-hidden="true"
      className={`inline-block shrink-0 bg-current ${className}`}
      style={{ maskImage: url, WebkitMaskImage: url, maskSize: "100% 100%", WebkitMaskSize: "100% 100%" }}
    />
  );
}
