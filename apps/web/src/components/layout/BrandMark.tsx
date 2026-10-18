import Icon from "@/components/ui/Icon";

// Purple asterisk tile + "Hookd" wordmark.
export default function BrandMark({ size = "md" }: { size?: "md" | "lg" }) {
  const large = size === "lg";
  return (
    <span className="inline-flex items-center gap-[9px]">
      <span
        className={`flex items-center justify-center rounded-[10px] bg-brand text-white ${large ? "size-9" : "size-[30px]"}`}
      >
        <Icon name="asterisk" className="size-[25px]" />
      </span>
      <span className={`text-ink ${large ? "text-[30px]" : "text-[25px]"} leading-none`}>Hookd</span>
    </span>
  );
}
