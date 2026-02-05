import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SidebarState {
  isCollapsed: boolean
  expandedSections: Record<string, boolean>
  toggleCollapse: () => void
  setCollapsed: (collapsed: boolean) => void
  toggleSection: (sectionTitle: string) => void
  setSectionExpanded: (sectionTitle: string, expanded: boolean) => void
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set) => ({
      isCollapsed: false,
      expandedSections: {
        Collect: true,
        Process: true,
        Create: true,
        Manage: false, // Manage section collapsed by default
      },
      toggleCollapse: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
      setCollapsed: (collapsed) => set({ isCollapsed: collapsed }),
      toggleSection: (sectionTitle) =>
        set((state) => ({
          expandedSections: {
            ...state.expandedSections,
            [sectionTitle]: !state.expandedSections[sectionTitle],
          },
        })),
      setSectionExpanded: (sectionTitle, expanded) =>
        set((state) => ({
          expandedSections: {
            ...state.expandedSections,
            [sectionTitle]: expanded,
          },
        })),
    }),
    {
      name: 'sidebar-storage',
    }
  )
)
