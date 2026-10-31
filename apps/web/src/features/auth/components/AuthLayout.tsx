import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import creatorsPhoto from "@/assets/images/login-creators.jpg";
import testimonialPhoto from "@/assets/images/login-testimonial.jpg";
import BrandMark from "@/components/layout/BrandMark";
import { buttonClass } from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";

// Two-panel layout shared by log in, sign up and confirm: the form on the left, the
// brand story photo on the right (large screens only).
export default function AuthLayout({
  eyebrow,
  title,
  subtitle,
  children,
  footer,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-canvas p-4 sm:p-6">
      <div className="flex w-full flex-col justify-between gap-10 px-2 pb-6 pt-4 sm:px-12 lg:w-1/2 lg:max-w-[696px] lg:px-[70px] lg:pt-[30px]">
        <div className="flex items-center justify-between gap-4">
          <Link to="/" aria-label="Hookd home">
            <BrandMark size="lg" />
          </Link>
          <Link to="/" className={`${buttonClass("secondary", "sm")} whitespace-nowrap`}>
            <Icon name="arrow-right" className="size-4 rotate-180" />
            Back to home
          </Link>
        </div>
        <div className="w-full max-w-[416px]">
          <div className="flex flex-col gap-3">
            <p className="text-xs font-semibold tracking-wide text-brand">{eyebrow}</p>
            <h1 className="text-[30px] leading-[1.15] text-ink sm:text-[36px] lg:whitespace-nowrap">{title}</h1>
            {subtitle && <p className="text-sm text-ink-muted">{subtitle}</p>}
          </div>
          <div className="mt-7">{children}</div>
          {footer && <div className="mt-7 text-center text-[13px] text-ink-muted">{footer}</div>}
        </div>
        <p className="text-[11px] text-ink-subtle">© {new Date().getFullYear()} Hookd</p>
      </div>

      <div className="relative hidden flex-1 overflow-hidden rounded-[24px] lg:block">
        <img src={creatorsPhoto} alt="" className="absolute inset-0 size-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-[rgba(39,32,50,0)] from-20% to-[rgba(39,32,50,0.9)]" />
        <p className="absolute left-9 top-9 inline-flex items-center gap-2 rounded-full bg-surface px-3.5 py-2 text-[11px] font-semibold text-ink">
          <Icon name="sparkles" className="size-3.5 text-brand" />
          GOOD THINGS HAPPEN TOGETHER.
        </p>
        <figure className="absolute bottom-14 left-11 right-11 flex max-w-[585px] flex-col gap-[26px]">
          <blockquote className="text-[32px] leading-[1.32] text-white">
            “We came for the organization. We stayed for the space to create something really good.”
          </blockquote>
          <figcaption className="flex items-center gap-3">
            <img src={testimonialPhoto} alt="" className="size-[42px] rounded-full object-cover" />
            <span>
              <span className="block text-[13px] font-semibold text-white">Avery Morgan</span>
              <span className="block text-[11px] text-[#e8e1ee]">Creative Director, Forma</span>
            </span>
          </figcaption>
        </figure>
      </div>
    </div>
  );
}
