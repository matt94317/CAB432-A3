import { type InputHTMLAttributes, useState } from "react";
import Icon from "@/components/ui/Icon";
import TextField from "@/components/ui/TextField";

// Password input with a show/hide toggle.
export default function PasswordField(
  props: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: string; hint?: string },
) {
  const [visible, setVisible] = useState(false);
  return (
    <TextField
      {...props}
      type={visible ? "text" : "password"}
      fieldSize="lg"
      trailing={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          className="flex size-8 items-center justify-center rounded-md text-ink-muted hover:text-ink"
        >
          <Icon name={visible ? "eye" : "eye-off"} className="size-[17px]" />
        </button>
      }
    />
  );
}
