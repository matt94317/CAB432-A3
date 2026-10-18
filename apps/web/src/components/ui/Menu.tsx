import { type ReactNode, useEffect, useId, useRef, useState } from "react";

export interface MenuItem {
  label: string;
  onSelect: () => void;
  danger?: boolean;
}

// A small dropdown for row and card actions. Closes on Escape, outside click or select.
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
  /** Open below the trigger, or above it (for triggers at the bottom of the screen). */
  side?: "bottom" | "top";
  triggerClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !ref.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
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
      {open && (
        <div
          id={menuId}
          role="menu"
          className={`absolute z-20 min-w-40 overflow-hidden rounded-lg border border-line bg-surface py-1 shadow-lg ${
            align === "right" ? "right-0" : "left-0"
          } ${side === "top" ? "bottom-full mb-1" : "mt-1"}`}
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
              className={`block w-full px-3 py-2 text-left text-[13px] hover:bg-canvas ${item.danger ? "text-danger" : "text-ink"}`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
