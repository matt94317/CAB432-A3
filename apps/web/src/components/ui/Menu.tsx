import { type CSSProperties, type ReactNode, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

export interface MenuItem {
  label: string;
  onSelect: () => void;
  danger?: boolean;
}

const GAP = 4;

// A small dropdown for row and card actions. Closes on Escape, outside click, scroll or
// select. Drawn in a portal with fixed positioning, so cards and tables with
// overflow-hidden can't clip it; flips above the trigger when there's no room below.
export default function Menu({
  label,
  items,
  trigger,
  align = "right",
  side = "bottom",
  triggerClassName = "",
}: {
  label: string;
  items: MenuItem[];
  trigger: ReactNode;
  align?: "left" | "right";
  /** Preferred side: below the trigger, or above it (for triggers at the bottom of the screen). */
  side?: "bottom" | "top";
  triggerClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<CSSProperties>({ visibility: "hidden" });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  // Measure before paint so the menu never flashes in the wrong place
  useLayoutEffect(() => {
    if (!open || !triggerRef.current || !menuRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const height = menuRef.current.offsetHeight;
    const roomBelow = window.innerHeight - rect.bottom - GAP;
    const roomAbove = rect.top - GAP;
    const up = side === "top" ? roomAbove >= height || roomBelow < height : roomBelow < height && roomAbove > roomBelow;
    setPosition({
      top: up ? rect.top - height - GAP : rect.bottom + GAP,
      ...(align === "right" ? { right: window.innerWidth - rect.right } : { left: rect.left }),
    });
  }, [open, side, align]);

  useEffect(() => {
    if (!open) {
      setPosition({ visibility: "hidden" });
      return;
    }
    const inside = (target: EventTarget | null) =>
      triggerRef.current?.contains(target as Node) || menuRef.current?.contains(target as Node);
    const onMouseDown = (event: MouseEvent) => !inside(event.target) && setOpen(false);
    const onKeyDown = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    const onMove = () => setOpen(false);
    document.addEventListener("mousedown", onMouseDown);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("scroll", onMove, true);
    window.addEventListener("resize", onMove);
    return () => {
      document.removeEventListener("mousedown", onMouseDown);
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("scroll", onMove, true);
      window.removeEventListener("resize", onMove);
    };
  }, [open]);

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((o) => !o)}
        className={triggerClassName}
      >
        {trigger}
      </button>
      {open &&
        createPortal(
          <div
            ref={menuRef}
            id={menuId}
            role="menu"
            style={position}
            className="fixed z-50 min-w-40 overflow-hidden rounded-lg border border-line bg-surface py-1 shadow-lg"
          >
            {items.map((item) => (
              <button
                key={item.label}
                type="button"
                role="menuitem"
                onClick={() => {
                  setOpen(false);
                  item.onSelect();
                }}
                className={`block w-full whitespace-nowrap px-3 py-2 text-left text-[13px] hover:bg-canvas ${item.danger ? "text-danger" : "text-ink"}`}
              >
                {item.label}
              </button>
            ))}
          </div>,
          document.body,
        )}
    </div>
  );
}
