import Badge from "@/components/ui/Badge";
import Icon, { type IconName } from "@/components/ui/Icon";
import { Container, Eyebrow, SectionHeading } from "./shared";

const STEPS: { icon: IconName; title: string; body: string; capabilities: string[] }[] = [
  {
    icon: "users-round",
    title: "Find your kind of creator",
    body: "Go beyond follower counts. Find authentic voices who share your values and speak to your people.",
    capabilities: ["Audience insights", "Curated shortlists"],
  },
  {
    icon: "clapperboard",
    title: "Make room for great content",
    body: "Keep briefs, feedback, and approvals together. Less chasing in inboxes. More creating together.",
    capabilities: ["Campaign workspaces", "Simple approvals"],
  },
  {
    icon: "chart",
    title: "See the real impact",
    body: "Follow every post from published to performing. Turn real-time insights into your next smart move.",
    capabilities: ["Live post tracking", "Shareable reporting"],
  },
];

export default function Workflow() {
  return (
    <section id="platform">
      <Container className="flex flex-col gap-12 py-16 lg:py-[88px]">
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div className="flex flex-col gap-3.5 lg:w-[690px]">
            <Eyebrow>LESS BUSYWORK. MORE GOOD WORK.</Eyebrow>
            <SectionHeading>From first hello to your next big hit.</SectionHeading>
          </div>
          <p className="text-sm leading-[1.7] text-ink-muted lg:w-[330px]">
            One connected workflow for the people, content, and moments that move your brand forward.
          </p>
        </div>

        <ol className="grid gap-6 lg:grid-cols-3">
          {STEPS.map((step, i) => (
            <li key={step.title} className="flex flex-col gap-5 rounded-xl border border-line bg-surface p-7">
              <div className="flex items-center justify-between">
                <span className="flex size-11 items-center justify-center rounded-xl bg-brand-soft">
                  <Icon name={step.icon} className="size-[22px] text-brand" />
                </span>
                <span className="text-xs leading-[1.45] text-ink-subtle">{String(i + 1).padStart(2, "0")}</span>
              </div>
              <h3 className="text-xl font-semibold leading-[1.45] text-ink">{step.title}</h3>
              <p className="text-sm leading-[1.7] text-ink-muted">{step.body}</p>
              <div className="flex flex-wrap gap-2">
                {step.capabilities.map((capability) => (
                  <Badge key={capability} dot={false}>
                    {capability}
                  </Badge>
                ))}
              </div>
            </li>
          ))}
        </ol>
      </Container>
    </section>
  );
}
