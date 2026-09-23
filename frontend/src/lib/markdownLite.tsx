import type { ReactNode } from 'react'

// Groq answers commonly include basic markdown (bold, italic, inline code).
// Rather than pull in a full markdown library for a RAG answer that's
// otherwise plain prose, render just these three inline forms safely as
// React nodes - never dangerouslySetInnerHTML, since this text ultimately
// originates from repository content the LLM was shown.
const INLINE_PATTERN = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g

export function renderInlineMarkdown(text: string): ReactNode[] {
  return text.split(INLINE_PATTERN).map((segment, index) => {
    if (segment.startsWith('**') && segment.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold">
          {segment.slice(2, -2)}
        </strong>
      )
    }
    if (segment.startsWith('`') && segment.endsWith('`')) {
      return (
        <code key={index} className="rounded bg-panel-2 px-1 py-0.5 font-mono text-[0.9em]">
          {segment.slice(1, -1)}
        </code>
      )
    }
    if (segment.startsWith('*') && segment.endsWith('*')) {
      return <em key={index}>{segment.slice(1, -1)}</em>
    }
    return segment
  })
}
