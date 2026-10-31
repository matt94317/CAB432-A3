import { useState } from "react";
import Badge from "@/components/ui/Badge";
import Icon from "@/components/ui/Icon";
import { ActionLink, Container, Eyebrow, SectionHeading } from "./shared";

type Billing = "monthly" | "yearly";

const PLANS = [
  {
    name: "Starter",
    tagline: "For your first great collaborations.",
    monthly: 49,
    yearly: 39,
    lead: "A little structure. A lot of possibility.",
    features: [
      "10 active creators",
      "3 active campaigns",
      "Content approvals & library",
      "Essential performance insights",
      "2 team members",
    ],
  },
  {
    name: "Pro",
    tagline: "For brands finding their momentum.",
    monthly: 149,
    yearly: 119,
    featured: true,
    lead: "Everything in Starter, and more room to grow.",
    features: [
      "50 active creators",
      "Unlimited campaigns",
      "Live post & engagement tracking",
      "Custom reports & exports",
      "5 team members + priority support",
    ],
  },
  {
    name: "Scale",
    tagline: "For big ideas and bigger communities.",
    monthly: 399,
    yearly: 319,
    lead: "Everything in Pro, built around your team.",
    features: [
      "Unlimited creator relationships",
      "Multiple brand workspaces",
      "Advanced analytics & API access",
      "Custom roles & permissions",
      "Dedicated success manager",
    ],
  },
];

export default function Pricing() {
  const [billing, setBilling] = useState<Billing>("monthly");

  return (
    <section id="pricing" className="flex flex-col gap-[35px]">
      <div className="flex flex-col items-center gap-3.5 text-center">
        <Eyebrow>ROOM TO START. SPACE TO GROW.</Eyebrow>
        <SectionHeading className="sm:leading-[1.45]">Good collaborations. Simple pricing.</SectionHeading>
        <p className="text-[15px] leading-[1.45] text-ink-muted">
          Manager plans: 7 days free with a card. Creators use Hookd free.
        </p>
        <div role="group" aria-label="Billing period" className="flex items-center gap-1.5 rounded-[10px] bg-warm p-1">
          <BillingOption value="monthly" current={billing} onSelect={setBilling}>
            Monthly
          </BillingOption>
          <BillingOption value="yearly" current={billing} onSelect={setBilling}>
            Yearly
          </BillingOption>
          <Badge tone="success" dot={false}>
            Save 20%
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`flex flex-col gap-[22px] rounded-[20px] p-[30px] ${
              plan.featured ? "border-[1.5px] border-brand bg-brand-soft" : "border border-line bg-surface"
            }`}
          >
            <div className="flex items-start justify-between">
              <h3 className="text-[21px] leading-[1.45] text-ink">{plan.name}</h3>
              {plan.featured && (
                <Badge tone="brand" dot={false}>
                  Most popular
                </Badge>
              )}
            </div>
            <p className="text-[13px] leading-[1.45] text-ink-muted">{plan.tagline}</p>
            <p className="flex items-baseline gap-[7px]">
              <span className="text-[46px] leading-[1.1] text-ink">${plan[billing]}</span>
              <span className="text-xs leading-[1.45] text-ink-muted">
                / month{billing === "yearly" && ", billed yearly"}
              </span>
            </p>
            <ActionLink to="/signup" variant={plan.featured ? "primary" : "secondary"} className="w-full">
              Try {plan.name} free
            </ActionLink>
            <div className="h-px bg-line" />
            <p className="text-[11px] leading-[1.45] text-ink-muted">{plan.lead}</p>
            <ul className="flex flex-col gap-4">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-center gap-[9px] text-xs leading-[1.45] text-ink">
                  <Icon name="tick" className="size-[15px] text-brand" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <p className="text-center text-xs leading-[1.45] text-ink-muted">
        Need a custom setup? We’ll find your fit. Talk to our team ↗
      </p>
    </section>
  );
}

function BillingOption({
  value,
  current,
  onSelect,
  children,
}: {
  value: Billing;
  current: Billing;
  onSelect: (value: Billing) => void;
  children: string;
}) {
  const selected = value === current;
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={() => onSelect(value)}
      className={`h-9 rounded-lg border px-[13px] text-xs leading-[1.45] transition ${
        selected ? "border-line bg-surface font-semibold text-ink" : "border-transparent text-ink-muted hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}
