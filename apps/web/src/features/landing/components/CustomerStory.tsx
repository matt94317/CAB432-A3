import quotePhoto from "@/assets/landing/quote-avatar.jpg";
import { Container, Eyebrow } from "./shared";

const OUTCOMES = [
  { value: "3.2×", label: "higher engagement" },
  { value: "12 hrs", label: "saved every week" },
  { value: "94%", label: "creator rebooking rate" },
];

export default function CustomerStory() {
  return (
    <section aria-label="Customer story" className="bg-[#272032]">
      <Container className="flex flex-col gap-12 py-16 lg:flex-row lg:items-center lg:gap-[70px]">
        <figure className="flex flex-col items-start gap-7 lg:flex-[0_1_770px]">
          <Eyebrow className="font-normal! text-brand-muted">GOOD PEOPLE. REAL RESULTS.</Eyebrow>
          <blockquote className="text-2xl font-medium leading-[1.4] text-white sm:text-[31px]">
            “Hookd gave us back the time to do what we love — build genuine relationships and create content that feels
            like us.”
          </blockquote>
          <figcaption className="flex items-center gap-3 leading-[1.45]">
            <img src={quotePhoto} alt="" className="size-11 rounded-full object-cover" />
            <span className="flex flex-col gap-[3px]">
              <span className="text-[13px] font-semibold text-white">Avery Morgan</span>
              <span className="text-xs text-[#c3b9d1]">Creative Director, Forma</span>
            </span>
          </figcaption>
          <p className="text-xs font-medium leading-[1.45] text-brand-muted">Read the Forma story ↗</p>
        </figure>

        <dl className="flex min-w-0 flex-1 flex-col gap-[26px] leading-[1.45]">
          {OUTCOMES.map((outcome) => (
            <div key={outcome.label} className="flex items-center gap-6">
              <dt className="w-[130px] shrink-0 text-[38px] font-semibold text-brand-muted">{outcome.value}</dt>
              <dd className="text-[13px] text-[#c3b9d1]">{outcome.label}</dd>
            </div>
          ))}
        </dl>
      </Container>
    </section>
  );
}
