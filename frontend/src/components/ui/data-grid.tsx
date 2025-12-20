'use client';

import { AgGridReact, AgGridReactProps } from 'ag-grid-react';
import { useRef, useMemo } from 'react';
import { cn } from '@/lib/utils';

// Ensure AG Grid is initialized
import '@/lib/ag-grid-config';

interface DataGridProps<T> extends AgGridReactProps<T> {
  className?: string;
  height?: string | number;
}

export function DataGrid<T>({
  className,
  height = 400,
  ...props
}: DataGridProps<T>) {
  const gridRef = useRef<AgGridReact<T>>(null);

  const defaultColDef = useMemo(() => ({
    sortable: true,
    resizable: true,
    filter: true,
  }), []);

  return (
    <div
      className={cn('ag-theme-custom w-full', className)}
      style={{ height }}
    >
      <AgGridReact<T>
        ref={gridRef}
        defaultColDef={defaultColDef}
        animateRows={true}
        {...props}
      />
    </div>
  );
}
