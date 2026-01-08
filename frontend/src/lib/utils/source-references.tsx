import React from 'react'
import { FileText, Lightbulb, FileEdit, FileSpreadsheet } from 'lucide-react'

export type ReferenceType = 'source' | 'note' | 'source_insight' | 'acm'

export interface ParsedReference {
  type: ReferenceType
  id: string
  originalText: string
  startIndex: number
  endIndex: number
  /** Optional field name for ACM references (e.g., 'product', 'risk_status') */
  field?: string
}

export interface ExtractedReference {
  type: ReferenceType
  id: string
  originalText: string
  placeholder: string
}

export interface ExtractedReferences {
  processedText: string
  references: ExtractedReference[]
}

export interface ReferenceData {
  number: number
  type: ReferenceType
  id: string
}

/**
 * Parse source references from text
 *
 * Handles various formats:
 * - [source:abc123] → single reference
 * - [note:a], [note:b] → multiple references
 * - [note:a, note:b] → comma-separated references (edge case from LLM)
 * - Mixed: [source:x, note:y, source_insight:z]
 * - [acm:record_id:field] → ACM cell reference (e.g., [acm:acm_record:abc123:product])
 *
 * @param text - Text containing references
 * @returns Array of parsed references
 */
export function parseSourceReferences(text: string): ParsedReference[] {
  const matches: ParsedReference[] = []

  // Match pattern: (source_insight|note|source):alphanumeric_id
  // This handles references both inside and outside brackets
  const standardPattern = /(source_insight|note|source):([a-zA-Z0-9_]+)/g

  let match
  while ((match = standardPattern.exec(text)) !== null) {
    const type = match[1] as ReferenceType
    const id = match[2]

    matches.push({
      type,
      id,
      originalText: match[0],
      startIndex: match.index,
      endIndex: standardPattern.lastIndex
    })
  }

  // Match ACM pattern: acm:table_name:record_id or acm:table_name:record_id:field
  // SurrealDB record IDs have format "table_name:record_id" (e.g., "acm_record:abc123")
  // Full pattern examples:
  //   [acm:acm_record:abc123] → recordId="acm_record:abc123", field=undefined
  //   [acm:acm_record:abc123:product] → recordId="acm_record:abc123", field="product"
  const acmPattern = /acm:([a-zA-Z_][a-zA-Z0-9_]*):([a-zA-Z0-9_]+)(?::([a-zA-Z_][a-zA-Z0-9_]*))?/g

  while ((match = acmPattern.exec(text)) !== null) {
    const tableName = match[1]  // e.g., "acm_record"
    const recordId = match[2]   // e.g., "abc123"
    const field = match[3] || undefined  // e.g., "product" or undefined

    // Reconstruct full SurrealDB record ID
    const fullRecordId = `${tableName}:${recordId}`

    matches.push({
      type: 'acm',
      id: fullRecordId,
      field,
      originalText: match[0],
      startIndex: match.index,
      endIndex: acmPattern.lastIndex
    })
  }

  // Sort by startIndex to maintain order
  matches.sort((a, b) => a.startIndex - b.startIndex)

  return matches
}

/**
 * Handler callbacks for different reference types
 */
export interface ReferenceClickHandlers {
  /** Called for source, note, source_insight references */
  onReferenceClick?: (type: ReferenceType, id: string) => void
  /** Called specifically for ACM references with record ID and optional field */
  onACMClick?: (recordId: string, field?: string) => void
}

/**
 * ACM Citation Link component - renders ACM references as styled clickable badges
 *
 * @param recordId - The SurrealDB record ID (e.g., "acm_record:abc123")
 * @param field - Optional field name to highlight (e.g., "product", "risk_status")
 * @param displayText - Text to display on the badge
 * @param onOpen - Callback when badge is clicked, receives recordId and field
 *
 * @example
 * <ACMCitationLink
 *   recordId="acm_record:abc123"
 *   field="product"
 *   displayText="ACM: product"
 *   onOpen={(id, field) => openViewer(id, field)}
 * />
 */
function ACMCitationLink({
  recordId,
  field,
  displayText,
  onOpen
}: {
  recordId: string
  field?: string
  displayText: string
  onOpen: (recordId: string, field?: string) => void
}) {
  return (
    <button
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        onOpen(recordId, field)
      }}
      className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium
                 bg-amber-100 text-amber-800 rounded hover:bg-amber-200
                 dark:bg-amber-900/50 dark:text-amber-200 dark:hover:bg-amber-900"
      type="button"
      title={`View ACM record: ${recordId}${field ? ` (${field})` : ''}`}
    >
      <FileSpreadsheet className="h-3 w-3" />
      {displayText}
    </button>
  )
}

/**
 * Convert source references in text to clickable React elements
 *
 * @param text - Text containing references
 * @param onReferenceClick - Callback when reference is clicked (type, id)
 * @returns React nodes with clickable reference buttons
 */
export function convertSourceReferences(
  text: string,
  onReferenceClick: (type: ReferenceType, id: string) => void
): React.ReactNode {
  const matches = parseSourceReferences(text)

  if (matches.length === 0) return text

  const parts: React.ReactNode[] = []
  let lastIndex = 0

  matches.forEach((match, idx) => {
    // Check if there are brackets before the match
    const beforeMatch = text.substring(Math.max(0, match.startIndex - 2), match.startIndex)
    const hasDoubleBracketBefore = beforeMatch === '[['
    const hasSingleBracketBefore = beforeMatch.endsWith('[') && !hasDoubleBracketBefore

    // Determine where to start including text
    let textStartIndex = lastIndex
    if (hasDoubleBracketBefore && lastIndex === match.startIndex - 2) {
      textStartIndex = match.startIndex - 2
    } else if (hasSingleBracketBefore && lastIndex === match.startIndex - 1) {
      textStartIndex = match.startIndex - 1
    }

    // Add text before match (excluding brackets we'll include in the button)
    if (textStartIndex < match.startIndex && lastIndex < textStartIndex) {
      parts.push(text.substring(lastIndex, textStartIndex))
    } else if (lastIndex < match.startIndex && !hasSingleBracketBefore && !hasDoubleBracketBefore) {
      parts.push(text.substring(lastIndex, match.startIndex))
    }

    // Check if there are brackets after the match
    const afterMatch = text.substring(match.endIndex, Math.min(text.length, match.endIndex + 2))
    const hasDoubleBracketAfter = afterMatch === ']]'
    const hasSingleBracketAfter = afterMatch.startsWith(']') && !hasDoubleBracketAfter

    // Determine the display text with appropriate brackets
    let displayText = match.originalText
    if (hasDoubleBracketBefore && hasDoubleBracketAfter) {
      displayText = `[[${match.originalText}]]`
    } else if (hasSingleBracketBefore && hasSingleBracketAfter) {
      displayText = `[${match.originalText}]`
    } else {
      displayText = match.originalText
    }

    // Add clickable reference button
    parts.push(
      <button
        key={`ref-${idx}-${match.type}-${match.id}`}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onReferenceClick(match.type, match.id)
        }}
        className="text-primary hover:underline cursor-pointer inline font-medium"
        type="button"
      >
        {displayText}
      </button>
    )

    // Update lastIndex to skip the closing brackets
    if (hasDoubleBracketAfter) {
      lastIndex = match.endIndex + 2
    } else if (hasSingleBracketAfter) {
      lastIndex = match.endIndex + 1
    } else {
      lastIndex = match.endIndex
    }
  })

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex))
  }

  return <>{parts}</>
}

/**
 * Convert source references in text to clickable React elements with extended handlers
 * Supports ACM references with dedicated handler
 *
 * @param text - Text containing references
 * @param handlers - Object with handlers for different reference types
 * @returns React nodes with clickable reference buttons
 */
export function convertSourceReferencesExtended(
  text: string,
  handlers: ReferenceClickHandlers
): React.ReactNode {
  const matches = parseSourceReferences(text)

  if (matches.length === 0) return text

  const parts: React.ReactNode[] = []
  let lastIndex = 0

  matches.forEach((match, idx) => {
    // Check if there are brackets before the match
    const beforeMatch = text.substring(Math.max(0, match.startIndex - 2), match.startIndex)
    const hasDoubleBracketBefore = beforeMatch === '[['
    const hasSingleBracketBefore = beforeMatch.endsWith('[') && !hasDoubleBracketBefore

    // Determine where to start including text
    let textStartIndex = lastIndex
    if (hasDoubleBracketBefore && lastIndex === match.startIndex - 2) {
      textStartIndex = match.startIndex - 2
    } else if (hasSingleBracketBefore && lastIndex === match.startIndex - 1) {
      textStartIndex = match.startIndex - 1
    }

    // Add text before match (excluding brackets we'll include in the button)
    if (textStartIndex < match.startIndex && lastIndex < textStartIndex) {
      parts.push(text.substring(lastIndex, textStartIndex))
    } else if (lastIndex < match.startIndex && !hasSingleBracketBefore && !hasDoubleBracketBefore) {
      parts.push(text.substring(lastIndex, match.startIndex))
    }

    // Check if there are brackets after the match
    const afterMatch = text.substring(match.endIndex, Math.min(text.length, match.endIndex + 2))
    const hasDoubleBracketAfter = afterMatch === ']]'
    const hasSingleBracketAfter = afterMatch.startsWith(']') && !hasDoubleBracketAfter

    // Determine the display text with appropriate brackets
    let displayText = match.originalText
    if (hasDoubleBracketBefore && hasDoubleBracketAfter) {
      displayText = `[[${match.originalText}]]`
    } else if (hasSingleBracketBefore && hasSingleBracketAfter) {
      displayText = `[${match.originalText}]`
    } else {
      displayText = match.originalText
    }

    // Add clickable reference component based on type
    if (match.type === 'acm' && handlers.onACMClick) {
      // Use ACM-specific styled component
      parts.push(
        <ACMCitationLink
          key={`acm-ref-${idx}-${match.id}`}
          recordId={match.id}
          field={match.field}
          displayText={match.field ? `ACM: ${match.field}` : 'ACM Record'}
          onOpen={handlers.onACMClick}
        />
      )
    } else if (handlers.onReferenceClick) {
      // Standard reference button
      parts.push(
        <button
          key={`ref-${idx}-${match.type}-${match.id}`}
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            handlers.onReferenceClick!(match.type, match.id)
          }}
          className="text-primary hover:underline cursor-pointer inline font-medium"
          type="button"
        >
          {displayText}
        </button>
      )
    } else {
      // No handler, just show as text
      parts.push(displayText)
    }

    // Update lastIndex to skip the closing brackets
    if (hasDoubleBracketAfter) {
      lastIndex = match.endIndex + 2
    } else if (hasSingleBracketAfter) {
      lastIndex = match.endIndex + 1
    } else {
      lastIndex = match.endIndex
    }
  })

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex))
  }

  return <>{parts}</>
}

/**
 * Convert references in text to markdown links
 * Use this BEFORE passing text to ReactMarkdown
 *
 * Handles complex patterns including:
 * - Plain references: source:abc → [source:abc](#ref-source-abc)
 * - Bracketed: [source:abc] → [[source:abc]](#ref-source-abc)
 * - Double brackets: [[source:abc]] → [[[source:abc]]](#ref-source-abc)
 * - With bold: [**source:abc**] → [**source:abc**](#ref-source-abc)
 * - After commas: [source:a, note:b] → each converted separately
 * - Nested: [**source:a**, [source_insight:b]] → both converted
 * - ACM references: [acm:record_id:field] → [acm:record_id:field](#ref-acm-record_id-field)
 *
 * Uses greedy matching to catch all references regardless of surrounding context.
 *
 * @param text - Original text with references
 * @returns Text with references converted to markdown links
 */
export function convertReferencesToMarkdownLinks(text: string): string {
  // Step 1: Find ALL references using simple greedy patterns
  const refPattern = /(source_insight|note|source):([a-zA-Z0-9_]+)/g
  // ACM pattern: acm:table_name:record_id or acm:table_name:record_id:field
  const acmPattern = /acm:([a-zA-Z_][a-zA-Z0-9_]*):([a-zA-Z0-9_]+)(?::([a-zA-Z_][a-zA-Z0-9_]*))?/g
  const references: Array<{ type: string; id: string; field?: string; index: number; length: number }> = []

  let match
  while ((match = refPattern.exec(text)) !== null) {
    const type = match[1]
    const id = match[2]

    // Validate the reference
    const validTypes = ['source', 'source_insight', 'note']
    if (!validTypes.includes(type) || !id || id.length === 0 || id.length > 100) {
      continue // Skip invalid references
    }

    references.push({
      type,
      id,
      index: match.index,
      length: match[0].length
    })
  }

  // Find ACM references - pattern matches table_name:record_id:optional_field
  while ((match = acmPattern.exec(text)) !== null) {
    const tableName = match[1]  // e.g., "acm_record"
    const recordId = match[2]   // e.g., "abc123"
    const field = match[3] || undefined  // e.g., "product" or undefined

    // Reconstruct full SurrealDB record ID
    const fullRecordId = `${tableName}:${recordId}`

    references.push({
      type: 'acm',
      id: fullRecordId,
      field,
      index: match.index,
      length: match[0].length
    })
  }

  // If no references found, return original text
  if (references.length === 0) return text

  // Sort by index (descending) for safe replacement from end to start
  references.sort((a, b) => b.index - a.index)

  // Step 2: Process references from end to start (to preserve indices)
  let result = text
  for (const ref of references) {
    const refStart = ref.index
    const refEnd = refStart + ref.length
    // Build the refText - for ACM include field if present
    const refText = ref.type === 'acm'
      ? (ref.field ? `acm:${ref.id}:${ref.field}` : `acm:${ref.id}`)
      : `${ref.type}:${ref.id}`

    // Step 3: Analyze context around the reference
    // Look back up to 50 chars for opening brackets/bold markers
    const contextBefore = result.substring(Math.max(0, refStart - 50), refStart)
    // Look ahead up to 50 chars for closing brackets/bold markers
    const contextAfter = result.substring(refEnd, Math.min(result.length, refEnd + 50))

    // Determine display text by checking immediate surroundings
    let displayText = refText
    let replaceStart = refStart
    let replaceEnd = refEnd

    // Check for double brackets [[ref]]
    if (contextBefore.endsWith('[[') && contextAfter.startsWith(']]')) {
      displayText = `[[${refText}]]`
      replaceStart = refStart - 2
      replaceEnd = refEnd + 2
    }
    // Check for single brackets [ref]
    else if (contextBefore.endsWith('[') && contextAfter.startsWith(']')) {
      displayText = `[${refText}]`
      replaceStart = refStart - 1
      replaceEnd = refEnd + 1
    }
    // Check for bold with brackets [**ref**]
    else if (contextBefore.endsWith('[**') && contextAfter.startsWith('**]')) {
      displayText = `[**${refText}**]`
      replaceStart = refStart - 3
      replaceEnd = refEnd + 3
    }
    // Check for just bold **ref**
    else if (contextBefore.endsWith('**') && contextAfter.startsWith('**')) {
      displayText = `**${refText}**`
      replaceStart = refStart - 2
      replaceEnd = refEnd + 2
    }
    // Plain reference (no brackets)
    else {
      displayText = refText
    }

    // Step 4: Build the markdown link
    // For ACM references, include field in href if present
    const href = ref.type === 'acm'
      ? (ref.field ? `#ref-acm-${ref.id}-${ref.field}` : `#ref-acm-${ref.id}`)
      : `#ref-${ref.type}-${ref.id}`
    const markdownLink = `[${displayText}](${href})`

    // Step 5: Replace in the result string
    result = result.substring(0, replaceStart) + markdownLink + result.substring(replaceEnd)
  }

  return result
}

/**
 * Create a custom link component for ReactMarkdown that handles reference links
 *
 * @param onReferenceClick - Callback for when a reference link is clicked
 * @returns React component for rendering links
 */
export function createReferenceLinkComponent(
  onReferenceClick: (type: ReferenceType, id: string) => void
) {
  const ReferenceLinkComponent = ({
    href,
    children,
    ...props
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & {
    href?: string
    children?: React.ReactNode
  }) => {
    // Check if this is a reference link (starts with #ref-)
    if (href?.startsWith('#ref-')) {
      // Parse: #ref-source-abc123 → type=source, id=abc123
      const parts = href.substring(5).split('-') // Remove '#ref-'
      const type = parts[0] as ReferenceType
      const id = parts.slice(1).join('-') // Rejoin in case ID has dashes

      // Select appropriate icon based on reference type
      const IconComponent =
        type === 'source' ? FileText :
        type === 'source_insight' ? Lightbulb :
        type === 'acm' ? FileSpreadsheet :
        FileEdit // note

      return (
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            onReferenceClick(type, id)
          }}
          className="text-primary hover:underline cursor-pointer inline font-medium"
          type="button"
        >
          <IconComponent className="h-3 w-3 inline mr-1" aria-hidden="true" />
          {children}
        </button>
      )
    }

    // Regular link - open in new tab
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" {...props} className="text-primary hover:underline">
        {children}
      </a>
    )
  }

  ReferenceLinkComponent.displayName = 'ReferenceLinkComponent'
  return ReferenceLinkComponent
}

/**
 * Create a custom link component for ReactMarkdown that handles reference links including ACM
 * This extended version supports a separate handler for ACM references
 *
 * @param handlers - Object with handlers for different reference types
 * @returns React component for rendering links
 */
export function createReferenceLinkComponentExtended(
  handlers: ReferenceClickHandlers
) {
  const ReferenceLinkComponentExtended = ({
    href,
    children,
    ...props
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & {
    href?: string
    children?: React.ReactNode
  }) => {
    // Check if this is a reference link (starts with #ref-)
    if (href?.startsWith('#ref-')) {
      // Parse: #ref-source-abc123 → type=source, id=abc123
      // Or for ACM: #ref-acm-recordId-field → type=acm, id=recordId, field=field
      const parts = href.substring(5).split('-') // Remove '#ref-'
      const type = parts[0] as ReferenceType

      if (type === 'acm' && handlers.onACMClick) {
        // ACM reference: #ref-acm-recordId or #ref-acm-recordId-field
        const recordId = parts[1]
        const field = parts.length > 2 ? parts.slice(2).join('-') : undefined

        return (
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              handlers.onACMClick!(recordId, field)
            }}
            className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium
                       bg-amber-100 text-amber-800 rounded hover:bg-amber-200
                       dark:bg-amber-900/50 dark:text-amber-200 dark:hover:bg-amber-900"
            type="button"
            title={`View ACM record: ${recordId}${field ? ` (${field})` : ''}`}
          >
            <FileSpreadsheet className="h-3 w-3" aria-hidden="true" />
            {children}
          </button>
        )
      }

      // Standard reference types
      const id = parts.slice(1).join('-') // Rejoin in case ID has dashes

      // Select appropriate icon based on reference type
      const IconComponent =
        type === 'source' ? FileText :
        type === 'source_insight' ? Lightbulb :
        type === 'acm' ? FileSpreadsheet :
        FileEdit // note

      return (
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            handlers.onReferenceClick?.(type, id)
          }}
          className="text-primary hover:underline cursor-pointer inline font-medium"
          type="button"
        >
          <IconComponent className="h-3 w-3 inline mr-1" aria-hidden="true" />
          {children}
        </button>
      )
    }

    // Regular link - open in new tab
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" {...props} className="text-primary hover:underline">
        {children}
      </a>
    )
  }

  ReferenceLinkComponentExtended.displayName = 'ReferenceLinkComponentExtended'
  return ReferenceLinkComponentExtended
}

/**
 * Convert references in text to compact numbered format with reference list
 *
 * This function transforms verbose inline references like [source:abc123] into
 * compact numbered citations [1], [2], etc., and appends a "References:" section
 * at the bottom of the message with the full reference details.
 *
 * Algorithm:
 * 1. Parse all references using parseSourceReferences()
 * 2. Build a reference map to deduplicate and assign numbers
 * 3. Replace inline references with numbered citations
 * 4. Append reference list at the bottom
 *
 * @param text - Original text with references
 * @returns Text with numbered citations and reference list appended
 *
 * @example
 * Input: "See [source:abc] and [note:xyz]. Also [source:abc] again."
 * Output: "See [1] and [2]. Also [1] again.\n\nReferences:\n[1] - [source:abc]\n[2] - [note:xyz]"
 */
export function convertReferencesToCompactMarkdown(text: string): string {
  // Step 1: Parse all references using existing function
  const references = parseSourceReferences(text)

  // Step 2: If no references found, return original text
  if (references.length === 0) {
    return text
  }

  // Step 3: Build reference map (deduplicate and assign numbers)
  // For ACM references, include field in key since same record with different fields are distinct citations
  const referenceMap = new Map<string, ReferenceData & { field?: string }>()
  let nextNumber = 1

  for (const reference of references) {
    // Include field for ACM references to differentiate citations to different fields
    const key = reference.type === 'acm' && reference.field
      ? `${reference.type}:${reference.id}:${reference.field}`
      : `${reference.type}:${reference.id}`
    if (!referenceMap.has(key)) {
      referenceMap.set(key, {
        number: nextNumber++,
        type: reference.type,
        id: reference.id,
        field: reference.field
      })
    }
  }

  // Step 4: Replace references with numbered citations (process from end to start)
  let result = text
  for (let i = references.length - 1; i >= 0; i--) {
    const reference = references[i]
    // Use same key format as above
    const key = reference.type === 'acm' && reference.field
      ? `${reference.type}:${reference.id}:${reference.field}`
      : `${reference.type}:${reference.id}`
    const refData = referenceMap.get(key)!
    const number = refData.number

    // Analyze context around the reference
    const refStart = reference.startIndex
    const refEnd = reference.endIndex
    const contextBefore = result.substring(Math.max(0, refStart - 2), refStart)
    const contextAfter = result.substring(refEnd, Math.min(result.length, refEnd + 2))

    // Determine what to replace based on bracket context
    let replaceStart = refStart
    let replaceEnd = refEnd

    // Check for double brackets [[ref]]
    if (contextBefore === '[[' && contextAfter.startsWith(']]')) {
      replaceStart = refStart - 2
      replaceEnd = refEnd + 2
    }
    // Check for single brackets [ref]
    else if (contextBefore.endsWith('[') && contextAfter.startsWith(']')) {
      replaceStart = refStart - 1
      replaceEnd = refEnd + 1
    }

    // Build the numbered citation with full reference in href
    // For ACM references, include field in href if present
    const citationHref = reference.type === 'acm' && reference.field
      ? `#ref-${reference.type}-${reference.id}-${reference.field}`
      : `#ref-${reference.type}-${reference.id}`
    const citationLink = `[${number}](${citationHref})`

    // Replace in the result string
    result = result.substring(0, replaceStart) + citationLink + result.substring(replaceEnd)
  }

  // Step 5: Build reference list
  const refListLines: string[] = ['\n\nReferences:']

  // Iterate through reference map in insertion order (Map preserves order)
  for (const [, refData] of referenceMap) {
    // For ACM references, include field in display and href
    const displayRef = refData.type === 'acm' && refData.field
      ? `${refData.type}:${refData.id}:${refData.field}`
      : `${refData.type}:${refData.id}`
    const href = refData.type === 'acm' && refData.field
      ? `#ref-${refData.type}-${refData.id}-${refData.field}`
      : `#ref-${refData.type}-${refData.id}`
    const refListItem = `[${refData.number}] - [${displayRef}](${href})`
    refListLines.push(refListItem)
  }

  // Step 6: Append reference list to result
  result = result + refListLines.join('\n')

  return result
}

/**
 * Create a custom link component for ReactMarkdown that handles compact reference links
 *
 * This component handles two types of reference links:
 * 1. Numbered citations in text: [1](#ref-source-abc123)
 * 2. Reference list items: [source:abc123](#ref-source-abc123)
 *
 * Both use the same href format: #ref-{type}-{id}
 * The component extracts the type and id from the href and triggers the click handler.
 *
 * @param onReferenceClick - Callback for when a reference link is clicked
 * @returns React component for rendering links in ReactMarkdown
 *
 * @example
 * const LinkComponent = createCompactReferenceLinkComponent((type, id) => openModal(type, id))
 * <ReactMarkdown components={{ a: LinkComponent }}>...</ReactMarkdown>
 */
export function createCompactReferenceLinkComponent(
  onReferenceClick: (type: ReferenceType, id: string) => void
) {
  const CompactReferenceLinkComponent = ({
    href,
    children,
    ...props
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & {
    href?: string
    children?: React.ReactNode
  }) => {
    // Check if this is a reference link (starts with #ref-)
    if (href?.startsWith('#ref-')) {
      // Parse: #ref-source-abc123 → type=source, id=abc123
      const parts = href.substring(5).split('-') // Remove '#ref-'
      const type = parts[0] as ReferenceType
      const id = parts.slice(1).join('-') // Rejoin in case ID has dashes

      return (
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            onReferenceClick(type, id)
          }}
          className="text-primary hover:underline cursor-pointer inline font-medium"
          type="button"
        >
          {children}
        </button>
      )
    }

    // Regular link - open in new tab
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" {...props} className="text-primary hover:underline">
        {children}
      </a>
    )
  }

  CompactReferenceLinkComponent.displayName = 'CompactReferenceLinkComponent'
  return CompactReferenceLinkComponent
}

/**
 * Legacy function for backward compatibility
 * Converts old Link-based references to new click handler approach
 *
 * @deprecated Use extractReferences + replacePlaceholdersWithButtons instead
 */
export function convertSourceReferencesLegacy(text: string): React.ReactNode {
  // For legacy support, just return text as-is
  // Components should migrate to new convertSourceReferences function
  return text
}
