"use client";

type SwitchProps = {
  checked: boolean;
  label: string;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
};

export function Switch({
  checked,
  label,
  onCheckedChange,
  disabled = false,
}: SwitchProps) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        aria-label={label}
        aria-checked={checked}
        aria-disabled={disabled}
        role="switch"
        disabled={disabled}
        onClick={() => onCheckedChange?.(!checked)}
        className={`relative h-7 w-12 rounded-full transition ${
          checked ? "bg-primary" : "bg-slate-300"
        } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
      >
        <span
          className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition ${
            checked ? "left-6" : "left-1"
          }`}
        />
      </button>
      <span className="text-sm text-slate-600">{label}</span>
    </div>
  );
}
