import { Link } from "react-router-dom";
import { useAuth } from "@/auth/AuthProvider";
import BrandMark from "@/components/layout/BrandMark";
import { buttonClass } from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import { Container } from "./shared";

const LINKS = [
  { label: "Platform", href: "#platform" },
  { label: "For brands", href: "#showcase" },
  { label: "For creators", href: "#creators" },
  { label: "Pricing", href: "#pricing" },
  { label: "Resources", href: "#faq" },
];

// Top bar: brand, section links, and log in / get started (or back to the app when signed in).
export default function LandingNav() {
  const { status } = useAuth();

  return (
    <header>
      <Container className="flex h-24 items-center justify-between gap-4">
        <Link to="/" aria-label="Hookd home">
          <BrandMark size="lg" />
        </Link>
        <nav aria-label="Main" className="hidden items-center gap-8 lg:flex">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-[13px] font-medium leading-[1.45] text-ink transition hover:text-brand"
            >
              {link.label}
            </a>
          ))}
        </nav>
        {status === "signedIn" ? (
          <Link to="/overview" className={`${buttonClass("primary")} whitespace-nowrap`}>
            <Icon name="arrow-up-right" />
            Open dashboard
          </Link>
        ) : (
          <div className="flex items-center gap-2 sm:gap-3">
            <Link to="/login" className={`${buttonClass("secondary")} whitespace-nowrap border-transparent!`}>
              Log in
            </Link>
            <Link to="/signup" className={`${buttonClass("primary")} whitespace-nowrap`}>
              <Icon name="arrow-up-right" className="size-4 max-sm:hidden" />
              Get started
            </Link>
          </div>
        )}
      </Container>
    </header>
  );
}
