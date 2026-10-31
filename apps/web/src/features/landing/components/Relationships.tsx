import relationshipsPhoto from "@/assets/landing/relationships.jpg";
import Icon from "@/components/ui/Icon";
import { Container, Eyebrow, SectionHeading } from "./shared";

const BENEFITS = [
  {
    title: "Your creator network, all together",
    body: "Save favorites, share notes, and remember the little details.",
  },
  {
    title: "Feedback without the back-and-forth",
    body: "Clear briefs and one place for every “love this, but…”",
  },
  {
    title: "More confidence in every decision",
    body: "Understand what resonates, then build on what works.",
  },
];

export default function Relationships() {
  return (
    <section id="creators">
      <Container className="flex flex-col items-center gap-12 py-16 lg:flex-row lg:py-[88px] xl:gap-20">
        <div className="relative aspect-[580/440] w-full overflow-hidden rounded-[20px] lg:w-auto lg:flex-[0_1_580px]">
          <img src={relationshipsPhoto} alt="" className="absolute inset-0 size-full object-cover" />
          <div className="absolute bottom-4 left-4 right-4 flex max-w-[380px] items-start gap-3 rounded-xl bg-surface p-[18px] sm:bottom-[29px] sm:left-6">
            <Icon name="heart-handshake" className="size-7 text-brand" />
            <p className="flex flex-col gap-[3px] leading-[1.45]">
              <span className="text-[13px] font-semibold text-ink">Not just a list. Your people.</span>
              <span className="text-[11px] text-ink-muted">Better relationships make better content.</span>
            </p>
          </div>
        </div>

        <div className="flex min-w-0 flex-1 flex-col items-start gap-[22px]">
          <Eyebrow>HUMAN AT HEART. POWERFUL BY DESIGN.</Eyebrow>
          <SectionHeading className="sm:text-[42px]!">
            Built for relationships,
            <br />
            not spreadsheets.
          </SectionHeading>
          <p className="text-[15px] leading-[1.7] text-ink-muted">
            Great UGC isn’t a transaction. It’s a collaboration. Give your team the space to build a creator community
            that grows with you.
          </p>
          <ul className="flex w-full flex-col gap-[18px]">
            {BENEFITS.map((benefit) => (
              <li key={benefit.title} className="flex gap-[13px]">
                <Icon name="check" className="size-[19px] text-brand" />
                <p className="flex flex-col gap-1 leading-[1.45]">
                  <span className="text-sm font-semibold text-ink">{benefit.title}</span>
                  <span className="text-xs text-ink-muted">{benefit.body}</span>
                </p>
              </li>
            ))}
          </ul>
          <a href="#platform" className="text-[13px] font-semibold leading-[1.45] text-brand hover:underline">
            Meet your new workflow →
          </a>
        </div>
      </Container>
    </section>
  );
}
