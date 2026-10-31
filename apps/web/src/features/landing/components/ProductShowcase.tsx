import previousTrend from "@/assets/landing/previous-period-trend.png";
import showcaseAvatar1 from "@/assets/landing/showcase-avatar-1.jpg";
import showcaseAvatar2 from "@/assets/landing/showcase-avatar-2.jpg";
import showcaseAvatar3 from "@/assets/landing/showcase-avatar-3.jpg";
import viewsTrend from "@/assets/landing/views-trend.svg";
import BrandMark from "@/components/layout/BrandMark";
import Badge from "@/components/ui/Badge";
import { buttonClass } from "@/components/ui/Button";
import Icon, { type IconName } from "@/components/ui/Icon";
import { ActionLink, AvatarStack, Container, Eyebrow, SectionHeading } from "./shared";

const NAV: { icon: IconName; label: string }[] = [
  { icon: "layout-dashboard", label: "Overview" },
  { icon: "megaphone", label: "Campaigns" },
  { icon: "users", label: "Creators" },
  { icon: "clapperboard", label: "Post tracking" },
];

const METRICS = [
  { label: "Total views", value: "1.28M", change: "↗ 24.6%" },
  { label: "Engagement rate", value: "5.8%", change: "↗ 1.2%" },
  { label: "Published posts", value: "48", change: "↗ 18.5%" },
  { label: "Active creators", value: "24", change: "↗ 6 new" },
];

const BENEFITS = ["One home for every collaboration", "Your whole team, in the loop", "Insights you can actually use"];

export default function ProductShowcase() {
  return (
    <section id="showcase" className="bg-brand-soft">
      <Container className="flex flex-col gap-[38px] pb-20 pt-16 lg:pt-[72px]">
        <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div className="flex flex-col gap-3 lg:w-[660px]">
            <Eyebrow>YOUR CAMPAIGN HQ</Eyebrow>
            <SectionHeading>A little clarity changes everything.</SectionHeading>
          </div>
          <ActionLink to="/signup" variant="secondary" icon="arrow-up-right" className="self-start sm:self-auto">
            Explore the platform
          </ActionLink>
        </div>

        <ProductPreview />

        <ul className="flex flex-col justify-between gap-3 sm:flex-row">
          {BENEFITS.map((benefit) => (
            <li key={benefit} className="flex items-center gap-[9px] text-xs leading-[1.45] text-brand-strong">
              <Icon name="check" className="size-4 text-brand" />
              {benefit}
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}

// A static picture of the overview dashboard, built from the app's own pieces.
function ProductPreview() {
  return (
    <div
      role="img"
      aria-label="The Hookd overview: views, engagement, published posts and a live campaign"
      className="flex overflow-hidden rounded-2xl border border-[#dcd3ed] bg-canvas shadow-[0px_20px_48px_0px_rgba(40,32,50,0.1)] lg:h-[506px]"
    >
      <div className="hidden w-48 shrink-0 flex-col gap-[30px] bg-surface p-[22px] lg:flex">
        <BrandMark />
        <p className="text-xs font-semibold leading-[1.45] text-ink">Forma studio⌄</p>
        <ul className="flex flex-col gap-[9px]">
          {NAV.map((item, i) => (
            <li
              key={item.label}
              className={`flex items-center gap-[9px] rounded-md p-2.5 text-[11px] leading-[1.45] ${
                i === 0 ? "bg-brand-soft text-brand" : "text-ink-muted"
              }`}
            >
              <Icon name={item.icon} />
              {item.label}
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-2.5 rounded-lg bg-canvas p-3 leading-[1.45]">
          <p className="text-[11px] font-semibold text-ink">Made for your next chapter.</p>
          <p className="text-[10px] text-ink-muted">Your Pro workspace is ready.</p>
          <p className="text-[10px] text-brand">Explore your plan →</p>
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-5 p-4 sm:p-7">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-[5px] leading-[1.45]">
            <p className="text-[23px] text-ink">Good morning, Avery ☀</p>
            <p className="text-[11px] text-ink-muted">Here’s what’s happening with your creator community.</p>
          </div>
          <span className={buttonClass("primary", "sm")}>
            <Icon name="plus" />
            Create campaign
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3.5 leading-[1.45] md:grid-cols-4">
          {METRICS.map((metric) => (
            <div key={metric.label} className="flex flex-col gap-[9px] rounded-[9px] border border-line bg-surface p-4">
              <p className="text-[10px] text-ink-muted">{metric.label}</p>
              <p className="text-2xl text-ink">{metric.value}</p>
              <p className="text-[10px] text-on-target">{metric.change}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-4 md:flex-row">
          <div className="flex min-w-0 flex-1 flex-col gap-4 rounded-[10px] bg-surface p-[18px]">
            <div className="flex items-start justify-between">
              <p className="text-[13px] font-semibold leading-[1.45] text-ink">Content performance</p>
              <Badge dot={false}>This month</Badge>
            </div>
            <div className="flex flex-col gap-3 text-[10px] leading-[1.45] text-ink-subtle">
              <div className="flex h-[145px] gap-4">
                <div className="flex w-[31px] flex-col justify-between">
                  {["400k", "300k", "200k", "100k", "0"].map((tick) => (
                    <span key={tick}>{tick}</span>
                  ))}
                </div>
                <div className="relative flex min-w-0 flex-1 flex-col justify-between">
                  {[0, 1, 2, 3, 4].map((line) => (
                    <div key={line} className="h-px w-full bg-line" />
                  ))}
                  <div className="absolute left-0 top-[5px] h-[135px] w-full">
                    <div className="absolute inset-[-0.54%_-0.19%_-0.93%_0]">
                      <img src={viewsTrend} alt="" className="block size-full max-w-none" />
                    </div>
                  </div>
                  <div className="absolute left-0 top-[38px] h-[104px] w-full">
                    <div className="absolute inset-[-0.74%_-0.12%_-0.96%_0]">
                      <img src={previousTrend} alt="" className="block size-full max-w-none" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-between pl-[47px]">
                {["Oct 01", "Oct 07", "Oct 14", "Oct 21", "Oct 31"].map((date) => (
                  <span key={date}>{date}</span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex shrink-0 flex-col items-start gap-[15px] rounded-[10px] bg-surface p-[18px] leading-[1.45] md:w-[259px]">
            <p className="text-[13px] font-semibold text-ink">Your campaigns, connected.</p>
            <Badge tone="success">Live campaign</Badge>
            <p className="text-lg font-semibold text-ink">Everyday, elevated</p>
            <p className="text-[11px] text-ink-muted">Forma · Oct 01 – Oct 31</p>
            <AvatarStack
              photos={[showcaseAvatar1, showcaseAvatar2, showcaseAvatar3]}
              size="size-[27px]"
              overlap="-mr-[7px]"
            />
            <div className="h-[5px] w-full max-w-[223px] overflow-hidden rounded-full bg-brand-soft">
              <div className="h-full w-3/4 rounded-full bg-brand" />
            </div>
            <p className="text-[10px] text-ink-muted">18 of 24 deliverables published</p>
          </div>
        </div>
      </div>
    </div>
  );
}
