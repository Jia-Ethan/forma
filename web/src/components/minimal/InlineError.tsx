type InlineErrorProps = {
  message?: string | null;
};

export function InlineError({ message }: InlineErrorProps) {
  return (
    <div className="inline-error" aria-live="polite">
      {message ? <p>{message}</p> : <span>&nbsp;</span>}
    </div>
  );
}
