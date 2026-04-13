export type SegmentOption<T extends string> = {
  value: T;
  label: string;
  description?: string;
};

type SegmentedControlProps<T extends string> = {
  label: string;
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
};

export function SegmentedControl<T extends string>({ label, options, value, onChange }: SegmentedControlProps<T>) {
  function focusByIndex(current: HTMLButtonElement, index: number) {
    const tabs = current.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
    tabs?.[index]?.focus();
  }

  return (
    <div className="segmented-control" role="tablist" aria-label={label}>
      {options.map((option, index) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            className={selected ? "segment active" : "segment"}
            onClick={() => onChange(option.value)}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight" || event.key === "ArrowDown") {
                event.preventDefault();
                const nextIndex = (index + 1) % options.length;
                onChange(options[nextIndex].value);
                focusByIndex(event.currentTarget, nextIndex);
              }

              if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
                event.preventDefault();
                const nextIndex = (index - 1 + options.length) % options.length;
                onChange(options[nextIndex].value);
                focusByIndex(event.currentTarget, nextIndex);
              }

              if (event.key === "Home") {
                event.preventDefault();
                onChange(options[0].value);
                focusByIndex(event.currentTarget, 0);
              }

              if (event.key === "End") {
                event.preventDefault();
                onChange(options[options.length - 1].value);
                focusByIndex(event.currentTarget, options.length - 1);
              }
            }}
          >
            <span>{option.label}</span>
            {option.description ? <small>{option.description}</small> : null}
          </button>
        );
      })}
    </div>
  );
}
