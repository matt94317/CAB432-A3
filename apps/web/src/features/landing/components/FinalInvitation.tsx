import ctaAvatar1 from "@/assets/landing/cta-avatar-1.jpg";
import ctaAvatar2 from "@/assets/landing/cta-avatar-2.jpg";
import ctaAvatar3 from "@/assets/landing/cta-avatar-3.jpg";
import ctaAvatar4 from "@/assets/landing/cta-avatar-4.jpg";
import ctaAvatar5 from "@/assets/landing/cta-avatar-5.jpg";
import { ActionLink, AvatarStack, Container } from "./shared";

export default function FinalInvitation() {
  return (
    <Container className="pb-[72px]">
      <div className="flex flex-col gap-8 rounded-[20px] bg-brand-soft p-8 sm:p-[54px] lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col items-start gap-4">
          <AvatarStack
            photos={[ctaAvatar1, ctaAvatar2, ctaAvatar3, ctaAvatar4, ctaAvatar5]}
            size="size-[34px]"
            overlap="-mr-[7px]"
          />
          <h2 className="text-[30px] font-semibold leading-[1.15] text-ink sm:text-[40px]">
            Your next great story starts here.
          </h2>
          <p className="text-[15px] leading-[1.45] text-ink-muted">
            Bring your people, your ideas, and your next big “what if.”
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-start gap-3 lg:items-center">
          <ActionLink to="/signup" icon="arrow-up-right">
            Let’s make something great
          </ActionLink>
          <p className="text-[11px] leading-[1.45] text-ink-muted">
            Managers: 7 days free with a card. Creators: always free.
          </p>
        </div>
      </div>
    </Container>
  );
}
