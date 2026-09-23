const STATUS_COLOR: Record<string, string> = {
  indexed: 'var(--green)',
  indexing: 'var(--amber)',
  failed: 'var(--red)',
}

export function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLOR[status] ?? 'var(--muted)'

  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-xs text-muted">
      <span
        aria-hidden
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {status}
    </span>
  )
}
