# Tech Spec: E9-S1 - Create Document Library View

> **Story:** E9-S1
> **Epic:** Document Library Management
> **Status:** Drafted
> **Created:** 2025-12-19

---

## Overview

Create a dedicated document library view for managing all uploaded ACM documents. This provides a centralized interface for organizing, monitoring, and maintaining the document collection with features like grid/list views, filtering, sorting, and quick actions.

---

## User Story

**As a** user
**I want** a dedicated view to manage all my uploaded documents
**So that** I can organize, monitor, and maintain my ACM document collection

---

## Acceptance Criteria

- [ ] Document Library page accessible from main navigation
- [ ] Grid/List view toggle for document display
- [ ] Show for each document: name, type, upload date, processing status, ACM record count
- [ ] Filter by: document type (SAMP, ACM Register, Other), processing status, date range
- [ ] Sort by: name, date, type, record count
- [ ] Search documents by name or content keywords
- [ ] Bulk selection with multi-select checkboxes
- [ ] Quick actions: View, Re-process, Delete, Download original

---

## Technical Design

### 1. Page Structure

#### Location: `frontend/src/app/(dashboard)/documents/page.tsx`

```tsx
import { DocumentLibrary } from "@/components/documents/DocumentLibrary";

export default function DocumentsPage() {
  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Document Library</h1>
          <p className="text-muted-foreground">
            Manage your ACM documents and SAMP files
          </p>
        </div>
        <UploadButton />
      </div>
      <DocumentLibrary />
    </div>
  );
}
```

### 2. Document Library Component

#### Location: `frontend/src/components/documents/DocumentLibrary.tsx`

```tsx
import { useState } from "react";
import { useDocuments } from "@/hooks/useDocuments";
import { DocumentGrid } from "./DocumentGrid";
import { DocumentList } from "./DocumentList";
import { DocumentFilters } from "./DocumentFilters";
import { ViewToggle } from "./ViewToggle";
import { BulkActions } from "./BulkActions";

interface DocumentFiltersState {
  search: string;
  type: string | null;
  status: string | null;
  dateFrom: Date | null;
  dateTo: Date | null;
  sortBy: "name" | "date" | "type" | "records";
  sortOrder: "asc" | "desc";
}

export function DocumentLibrary() {
  const [view, setView] = useState<"grid" | "list">("grid");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<DocumentFiltersState>({
    search: "",
    type: null,
    status: null,
    dateFrom: null,
    dateTo: null,
    sortBy: "date",
    sortOrder: "desc",
  });

  const { documents, isLoading, refetch } = useDocuments(filters);

  const handleSelectAll = () => {
    if (selectedIds.size === documents.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(documents.map((d) => d.id)));
    }
  };

  const handleSelectOne = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4">
        <DocumentFilters filters={filters} onChange={setFilters} />
        <div className="flex-1" />
        <ViewToggle view={view} onChange={setView} />
      </div>

      {/* Bulk Actions (shown when items selected) */}
      {selectedIds.size > 0 && (
        <BulkActions
          selectedCount={selectedIds.size}
          selectedIds={Array.from(selectedIds)}
          onClearSelection={() => setSelectedIds(new Set())}
          onActionComplete={refetch}
        />
      )}

      {/* Document Display */}
      {view === "grid" ? (
        <DocumentGrid
          documents={documents}
          isLoading={isLoading}
          selectedIds={selectedIds}
          onSelect={handleSelectOne}
          onSelectAll={handleSelectAll}
        />
      ) : (
        <DocumentList
          documents={documents}
          isLoading={isLoading}
          selectedIds={selectedIds}
          onSelect={handleSelectOne}
          onSelectAll={handleSelectAll}
        />
      )}
    </div>
  );
}
```

### 3. Document Card (Grid View)

#### Location: `frontend/src/components/documents/DocumentCard.tsx`

```tsx
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { FileText, MoreVertical, Eye, RefreshCw, Trash, Download } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface DocumentCardProps {
  document: Document;
  isSelected: boolean;
  onSelect: () => void;
  onAction: (action: string) => void;
}

export function DocumentCard({
  document,
  isSelected,
  onSelect,
  onAction,
}: DocumentCardProps) {
  const statusColors = {
    completed: "bg-green-100 text-green-800",
    processing: "bg-blue-100 text-blue-800",
    failed: "bg-red-100 text-red-800",
    pending: "bg-gray-100 text-gray-800",
  };

  const typeIcons = {
    SAMP: "📋",
    "ACM Register": "⚠️",
    Other: "📄",
  };

  return (
    <Card className={cn("relative transition-shadow hover:shadow-md", isSelected && "ring-2 ring-primary")}>
      {/* Selection Checkbox */}
      <div className="absolute top-3 left-3 z-10">
        <Checkbox checked={isSelected} onCheckedChange={onSelect} />
      </div>

      <CardHeader className="pt-10">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{typeIcons[document.type] || "📄"}</span>
            <div>
              <h3 className="font-medium line-clamp-1">{document.name}</h3>
              <p className="text-sm text-muted-foreground">
                {formatDate(document.uploaded_at)}
              </p>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger>
              <MoreVertical className="w-5 h-5" />
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => onAction("view")}>
                <Eye className="w-4 h-4 mr-2" /> View
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction("reprocess")}>
                <RefreshCw className="w-4 h-4 mr-2" /> Re-process
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction("download")}>
                <Download className="w-4 h-4 mr-2" /> Download
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onAction("delete")}
                className="text-destructive"
              >
                <Trash className="w-4 h-4 mr-2" /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{document.type}</Badge>
          <Badge className={statusColors[document.status]}>
            {document.status}
          </Badge>
        </div>
      </CardContent>

      <CardFooter className="text-sm text-muted-foreground">
        {document.acm_record_count > 0 ? (
          <span>{document.acm_record_count} ACM records</span>
        ) : (
          <span>No ACM data extracted</span>
        )}
      </CardFooter>
    </Card>
  );
}
```

### 4. Document Filters Component

#### Location: `frontend/src/components/documents/DocumentFilters.tsx`

```tsx
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { Search, X } from "lucide-react";

export function DocumentFilters({ filters, onChange }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search documents..."
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="pl-9 w-[250px]"
        />
        {filters.search && (
          <button
            onClick={() => onChange({ ...filters, search: "" })}
            className="absolute right-3 top-1/2 -translate-y-1/2"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Document Type */}
      <Select
        value={filters.type || "all"}
        onValueChange={(v) => onChange({ ...filters, type: v === "all" ? null : v })}
      >
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="All Types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Types</SelectItem>
          <SelectItem value="SAMP">SAMP</SelectItem>
          <SelectItem value="ACM Register">ACM Register</SelectItem>
          <SelectItem value="Other">Other</SelectItem>
        </SelectContent>
      </Select>

      {/* Processing Status */}
      <Select
        value={filters.status || "all"}
        onValueChange={(v) => onChange({ ...filters, status: v === "all" ? null : v })}
      >
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="All Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Status</SelectItem>
          <SelectItem value="completed">Completed</SelectItem>
          <SelectItem value="processing">Processing</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
        </SelectContent>
      </Select>

      {/* Sort By */}
      <Select
        value={`${filters.sortBy}-${filters.sortOrder}`}
        onValueChange={(v) => {
          const [sortBy, sortOrder] = v.split("-");
          onChange({ ...filters, sortBy, sortOrder });
        }}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="date-desc">Newest First</SelectItem>
          <SelectItem value="date-asc">Oldest First</SelectItem>
          <SelectItem value="name-asc">Name (A-Z)</SelectItem>
          <SelectItem value="name-desc">Name (Z-A)</SelectItem>
          <SelectItem value="records-desc">Most Records</SelectItem>
          <SelectItem value="records-asc">Fewest Records</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
```

### 5. Documents API Hook

#### Location: `frontend/src/hooks/useDocuments.ts`

```tsx
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";

interface DocumentsFilters {
  search?: string;
  type?: string | null;
  status?: string | null;
  dateFrom?: Date | null;
  dateTo?: Date | null;
  sortBy?: string;
  sortOrder?: string;
}

export function useDocuments(filters: DocumentsFilters = {}) {
  return useQuery({
    queryKey: ["documents", filters],
    queryFn: async () => {
      const params = new URLSearchParams();

      if (filters.search) params.set("search", filters.search);
      if (filters.type) params.set("type", filters.type);
      if (filters.status) params.set("status", filters.status);
      if (filters.dateFrom) params.set("date_from", filters.dateFrom.toISOString());
      if (filters.dateTo) params.set("date_to", filters.dateTo.toISOString());
      if (filters.sortBy) params.set("sort_by", filters.sortBy);
      if (filters.sortOrder) params.set("sort_order", filters.sortOrder);

      const response = await apiClient.get(`/api/sources?${params.toString()}`);
      return response.data;
    },
    staleTime: 30000, // 30 seconds
  });
}
```

### 6. Backend API Enhancement

#### Update: `api/routers/source.py`

```python
@router.get("/sources")
async def list_sources(
    search: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
):
    """
    List sources with filtering, sorting, and ACM record counts.
    """
    query = "SELECT * FROM source"
    filters = []

    if search:
        filters.append(f"(title CONTAINS '{search}' OR content CONTAINS '{search}')")
    if type:
        filters.append(f"document_type = '{type}'")
    if status:
        filters.append(f"processing_status = '{status}'")
    if date_from:
        filters.append(f"created_at >= '{date_from.isoformat()}'")
    if date_to:
        filters.append(f"created_at <= '{date_to.isoformat()}'")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    # Sort
    sort_direction = "DESC" if sort_order == "desc" else "ASC"
    query += f" ORDER BY {sort_by} {sort_direction}"

    # Paginate
    offset = (page - 1) * page_size
    query += f" LIMIT {page_size} START {offset}"

    sources = await db.query(query)

    # Add ACM record counts
    for source in sources:
        source["acm_record_count"] = await db.query(
            f"SELECT count() FROM acm_record WHERE source_id = '{source['id']}'"
        )[0]["count"]

    return sources
```

### 7. Navigation Update

#### Update: `frontend/src/components/layout/AppSidebar.tsx`

```tsx
// Add Documents to navigation
{
  title: "Collect",
  items: [
    { name: "Documents", href: "/documents", icon: FolderOpen },  // NEW
    { name: "Sources", href: "/sources", icon: FileText },
    { name: "ACM Register", href: "/acm", icon: FileWarning },
  ],
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/documents/page.tsx` | New page |
| `frontend/src/components/documents/DocumentLibrary.tsx` | New component |
| `frontend/src/components/documents/DocumentCard.tsx` | New component |
| `frontend/src/components/documents/DocumentGrid.tsx` | New component |
| `frontend/src/components/documents/DocumentList.tsx` | New component |
| `frontend/src/components/documents/DocumentFilters.tsx` | New component |
| `frontend/src/components/documents/ViewToggle.tsx` | New component |
| `frontend/src/components/documents/BulkActions.tsx` | New component |
| `frontend/src/hooks/useDocuments.ts` | New hook |
| `api/routers/source.py` | Enhance list endpoint |
| `frontend/src/components/layout/AppSidebar.tsx` | Add navigation |

---

## Dependencies

- E1-S4: ACM API Endpoints (for ACM record counts)
- Existing Source model and API

---

## Testing

1. Navigate to /documents page
2. Verify documents load with correct metadata
3. Test grid/list view toggle
4. Test each filter (type, status, date range)
5. Test sorting options
6. Test search functionality
7. Test bulk selection
8. Test quick actions (view, reprocess, delete, download)
9. Test with empty library (show appropriate empty state)

---

## Estimated Complexity

**Medium** - Multiple components but follows existing patterns

---
