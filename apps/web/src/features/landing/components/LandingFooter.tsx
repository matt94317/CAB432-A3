import BrandMark from "@/components/layout/BrandMark";
import Icon from "@/components/ui/Icon";
import { Container } from "./shared";

// Links point at the matching section of this page where there is one.
const GROUPS: { title: string; links: { label: string; href?: string }[] }[] = [
  {
    title: "Platform",
    links: [
      { label: "Creator discovery", href: "#platform" },
      { label: "Campaign management", href: "#showcase" },
      { label: "Post tracking", href: "#showcase" },
      { label: "Analytics & reporting", href: "#showcase" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Customer stories" },
      { label: "The Hookd journal" },
      { label: "UGC playbook" },
      { label: "Help center", href: "#faq" },
    ],
  },
  {
    title: "Company",
    links: [{ label: "About Hookd" }, { label: "For creators", href: "#creators" }, { label: "Careers" }, { label: "Contact" }],
  },
];

export default function LandingFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <Container className="flex flex-col gap-[50px] pb-7 pt-[54px]">
        <div className="grid gap-10 sm:grid-cols-3 lg:flex lg:justify-between">
          <div className="flex flex-col gap-[18px] sm:col-span-3 lg:w-[370px]">
            <BrandMark size="lg" />
            <p className="w-[265px] text-[13px] leading-[1.7] text-ink-muted">
              Real people. Better content.
              <br />A home for your creator community.
            </p>
            <div aria-hidden="true" className="flex gap-[18px] text-ink-muted">
              <Icon name="instagram" className="size-[18px]" />
              <Icon name="linkedin" className="size-[18px]" />
              <Icon name="youtube" className="size-[18px]" />
            </div>
          </div>
          {GROUPS.map((group) => (
            <nav key={group.title} aria-label={group.title} className="lg:w-[195px]">
              <h2 className="text-xs leading-[1.45] text-ink">{group.title}</h2>
              <ul className="mt-[17px] flex flex-col gap-[17px] text-xs leading-[1.45] text-ink-muted">
                {group.links.map((link) => (
                  <li key={link.label}>
                    {link.href ? (
                      <a href={link.href} className="hover:text-ink">
                        {link.label}
                      </a>
                    ) : (
                      link.label
                    )}
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="flex flex-col justify-between gap-3 border-t border-line pt-[22px] text-[11px] leading-[1.45] sm:flex-row">
          <p className="text-ink-subtle">© {new Date().getFullYear()} Hookd. Made for good company.</p>
          <ul className="flex flex-wrap gap-6 text-ink-muted">
            <li>Privacy policy</li>
            <li>Terms of service</li>
            <li>Cookie settings</li>
          </ul>
        </div>
      </Container>
    </footer>
  );
}
