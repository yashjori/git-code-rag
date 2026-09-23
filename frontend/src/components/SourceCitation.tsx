import type { SourceReference } from '../api/types'

// The signature element: sources render as a real editor gutter (line
// range, right-aligned, hairline rule, file path) rather than a generic
// pill or card - because "here's the exact file and lines" is the whole
// point of this tool.
export function SourceCitations({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) return null

  return (
    <div className="mt-3 overflow-hidden rounded border border-line">
      <p className="border-b border-line bg-panel-2 px-3 py-1.5 font-mono text-[11px] uppercase tracking-wide text-muted">
        Sources
      </p>
      <div>
        {sources.map((source, index) => (
          <div
            key={`${source.file_path}-${source.start_line}-${index}`}
            className="flex items-stretch font-mono text-xs hover:bg-panel-2"
          >
            <span className="w-20 shrink-0 border-r border-line px-2 py-1.5 text-right text-muted tabular-nums">
              {source.start_line}
              {source.end_line !== source.start_line ? `–${source.end_line}` : ''}
            </span>
            <span className="px-3 py-1.5 text-fg">{source.file_path}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
