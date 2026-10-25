import icon from "@/assets/images/hookd-icon.png";
import wordmark from "@/assets/images/hookd-wordmark.png";

// Purple "H" tile + "hookd" wordmark.
export default function BrandMark({ size = "md" }: { size?: "md" | "lg" }) {
  const large = size === "lg";
  return (
    <span className="inline-flex items-center gap-[9px]">
      <img src={icon} alt="" className={large ? "size-9" : "size-[30px]"} />
      <img src={wordmark} alt="Hookd" className={large ? "h-[30px] w-auto" : "h-[25px] w-auto"} />
    </span>
  );
}
