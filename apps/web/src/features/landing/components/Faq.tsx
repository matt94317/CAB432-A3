import { useId, useState } from "react";
import Icon from "@/components/ui/Icon";
import { Eyebrow } from "./shared";

const QUESTIONS = [
  {
    question: "Is Hookd right for a small team?",
    answer:
      "Absolutely. Whether you’re running your first creator campaign or your fiftieth, Hookd keeps the moving pieces together — without adding more to your plate.",
  },
  {
    question: "Can I bring my existing creators?",
    answer:
      "Yes. Add the creators you already work with by their handle, assign them to a campaign, and Hookd starts following their posts straight away.",
  },
  {
    question: "Which social platforms can I track?",
    answer:
      "TikTok, for now. Hookd matches each creator’s posts to your campaign by its tracking hashtag and keeps their views and engagement up to date.",
  },
  {
    question: "Can I change or cancel my plan?",
    answer:
      "Any time. Move between plans as your team grows, or cancel before your 7-day trial ends and you won’t be charged.",
  },
];

export default function Faq() {
  const [open, setOpen] = useState<number | null>(0);
  const id = useId();

  return (
    <section id="faq" className="flex flex-col gap-12 lg:flex-row lg:gap-[90px]">
      <div className="flex flex-col items-start gap-[17px] lg:w-[410px] lg:shrink-0">
        <Eyebrow>A FEW THINGS YOU MIGHT BE WONDERING</Eyebrow>
        <h2 className="text-[30px] font-semibold leading-[1.2] text-ink sm:text-[35px]">
          Good questions.
          <br />
          Straight answers.
        </h2>
        <p className="text-[13px] leading-[1.45] text-ink-muted">
          Still curious about something? We’re real people, and we’d love to help.
        </p>
        <p className="text-[13px] font-semibold leading-[1.45] text-brand">Let’s talk →</p>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-[22px]">
        {QUESTIONS.map((item, i) => {
          const expanded = open === i;
          return (
            <div key={item.question} className="flex flex-col gap-3 border-b border-line pb-[22px]">
              <h3>
                <button
                  type="button"
                  aria-expanded={expanded}
                  aria-controls={`${id}-${i}`}
                  onClick={() => setOpen(expanded ? null : i)}
                  className={`flex w-full items-start justify-between gap-4 text-left text-[15px] leading-[1.45] text-ink ${
                    expanded ? "font-semibold" : "font-medium"
                  }`}
                >
                  {item.question}
                  <Icon
                    name={expanded ? "minus" : "plus"}
                    className={expanded ? "size-[18px] text-brand" : "size-[17px] text-ink-muted"}
                  />
                </button>
              </h3>
              <p id={`${id}-${i}`} hidden={!expanded} className="text-[13px] leading-[1.7] text-ink-muted">
                {item.answer}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
