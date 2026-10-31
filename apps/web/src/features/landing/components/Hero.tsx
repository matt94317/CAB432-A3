import heroAvatar1 from "@/assets/landing/hero-avatar-1.jpg";
import heroAvatar2 from "@/assets/landing/hero-avatar-2.jpg";
import heroAvatar3 from "@/assets/landing/hero-avatar-3.jpg";
import heroAvatar4 from "@/assets/landing/hero-avatar-4.jpg";
import featuredPhoto from "@/assets/landing/hero-featured.jpg";
import matchPhoto from "@/assets/landing/hero-match.jpg";
import secondaryPhoto from "@/assets/landing/hero-secondary.jpg";
import Badge from "@/components/ui/Badge";
import Icon from "@/components/ui/Icon";
import { ActionLink, AvatarStack, Container, ScaledCanvas } from "./shared";

export default function Hero() {
  return (
    <Container className="flex flex-col items-center gap-14 pb-20 pt-10 sm:pt-16 xl:flex-row xl:gap-[52px]">
      <div className="flex w-full max-w-[585px] flex-col items-start gap-7 xl:shrink-0">
        <p className="flex items-center gap-2">
          <Badge tone="brand" dot={false}>
            MADE FOR REAL CONNECTION
          </Badge>
          <Icon name="arrow-up-right" className="size-3.5 text-brand" />
        </p>
        <h1 className="text-[44px] leading-[1.04] text-ink sm:text-[58px] lg:text-[70px]">
          Real creators.
          <br />
          Remarkable
          <br />
          <span className="text-brand">brand stories.</span>
        </h1>
        <p className="max-w-[475px] text-[17px] leading-[1.7] text-ink-muted">
          Your next great campaign starts with a real connection. Discover creators, bring content to life, and see
          what’s working — all in Hookd.
        </p>
        <div className="flex flex-wrap gap-3">
          <ActionLink to="/signup" icon="arrow-up-right">
            Start your 7-day trial
          </ActionLink>
          <ActionLink to="#showcase" variant="secondary" icon="play">
            See Hookd in action
          </ActionLink>
        </div>
        <p className="flex gap-4 text-[11px] leading-[1.45] text-ink-muted">
          <span>✓ 7 days free</span>
          <span>✓ Card required</span>
        </p>
        <div className="flex items-center gap-[13px]">
          <AvatarStack
            photos={[heroAvatar1, heroAvatar2, heroAvatar3, heroAvatar4]}
            size="size-8"
            overlap="-mr-2"
          />
          <p className="flex flex-col gap-[3px] leading-[1.45]">
            <span className="text-xs text-brand" aria-label="Rated 5 out of 5">
              ★★★★★
            </span>
            <span className="text-[11px] text-ink-muted">Loved by 2,000+ growing brands</span>
          </p>
        </div>
      </div>

      <div aria-hidden="true" className="flex w-full min-w-0 justify-center xl:flex-1">
        <CreatorCollage />
      </div>
    </Container>
  );
}

// Tilted creator stories with floating "match" and "results" cards, drawn at 643×570.
function CreatorCollage() {
  return (
    <ScaledCanvas width={643} height={570} className="mt-6 xl:mt-0">
      <div className="absolute left-6 top-6 h-[506px] w-[590px] rounded-[28px] bg-brand-soft" />

      <div className="absolute left-[38px] top-[-22.46px] flex h-[497.3px] w-[354.42px] items-center justify-center">
        <div className="relative h-[476px] w-[322px] -rotate-4 overflow-hidden rounded-[20px] drop-shadow-[0px_20px_24px_rgba(40,32,50,0.1)]">
          <img src={featuredPhoto} alt="" className="absolute inset-0 size-full object-cover" />
          <span className="absolute left-4 top-4 flex items-center gap-1.5 rounded-full bg-surface px-2.5 py-1.5 text-[10px] font-semibold leading-[1.45] text-ink">
            <Icon name="video" className="size-[13px]" />
            Made by Maya
          </span>
          <span className="absolute left-4 top-[365px] flex w-[290px] flex-col gap-1 rounded-xl bg-surface p-4 leading-[1.45]">
            <span className="text-[11px] text-ink-muted">FORMA · EVERYDAY, ELEVATED</span>
            <span className="text-lg text-ink">A little everyday magic.</span>
          </span>
        </div>
      </div>

      <div className="absolute left-[348.89px] top-24 flex h-[353.3px] w-[264.21px] items-center justify-center">
        <div className="relative h-[334px] w-[236px] rotate-5 overflow-hidden rounded-[18px] drop-shadow-[0px_8px_16px_rgba(40,32,50,0.05)]">
          <img src={secondaryPhoto} alt="" className="absolute inset-0 size-full object-cover" />
          <span className="absolute left-[88px] top-[135px] flex size-[54px] items-center justify-center rounded-full bg-white/79">
            <Icon name="play" className="size-5 text-ink" />
          </span>
        </div>
      </div>

      <div className="absolute left-[344px] top-[18px] flex w-[263px] items-center gap-2.5 rounded-xl bg-surface p-3.5 shadow-[0px_8px_32px_0px_rgba(40,32,50,0.05)]">
        <img src={matchPhoto} alt="" className="size-[38px] rounded-full object-cover" />
        <span className="flex flex-col gap-[3px] leading-[1.45]">
          <span className="text-xs font-semibold text-ink">Your next great match.</span>
          <span className="text-[10px] text-ink-muted">Leo Chen · Lifestyle creator</span>
        </span>
        <Icon name="check" className="size-5 text-on-target" />
      </div>

      <div className="absolute left-[232px] top-[460px] flex w-[328px] items-center gap-4 rounded-[14px] bg-surface p-5 shadow-[0px_20px_48px_0px_rgba(40,32,50,0.1)]">
        <span className="flex size-[45px] items-center justify-center rounded-xl bg-on-target-soft">
          <Icon name="trending-up" className="size-6 text-on-target" />
        </span>
        <span className="flex flex-col gap-1">
          <span className="text-[11px] leading-[1.45] text-ink-muted">More connection. More impact.</span>
          <span className="leading-[1.45]">
            <span className="text-[25px] text-ink">3.2× </span>
            <span className="text-xs text-ink-muted">campaign engagement</span>
          </span>
        </span>
      </div>
    </ScaledCanvas>
  );
}
