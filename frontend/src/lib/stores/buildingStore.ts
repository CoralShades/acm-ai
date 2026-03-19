import { create } from 'zustand'

export type BuildingStreamStatus = 'detected' | 'extracting' | 'validating' | 'saving' | 'complete' | 'error'

interface BuildingStoreState {
  selectedBuildingId: string | null
  setSelectedBuilding: (id: string | null) => void
  buildingStatus: Map<string, BuildingStreamStatus>
  setBuildingStatus: (buildingId: string, status: BuildingStreamStatus) => void
  clearBuildingStatuses: () => void
  // Building selection for bulk export (E34-S2) — separate from selectedBuildingId (the viewed building)
  selectedBuildingIds: Set<string>
  toggleBuildingSelection: (id: string) => void
  selectAllBuildings: (ids: string[]) => void
  clearBuildingSelections: () => void
}

export const useBuildingStore = create<BuildingStoreState>((set) => ({
  selectedBuildingId: null,
  setSelectedBuilding: (id) => set({ selectedBuildingId: id }),
  buildingStatus: new Map(),
  setBuildingStatus: (buildingId, status) =>
    set((state) => {
      const next = new Map(state.buildingStatus)
      next.set(buildingId, status)
      return { buildingStatus: next }
    }),
  clearBuildingStatuses: () => set({ buildingStatus: new Map() }),
  // Building selection for bulk export (E34-S2)
  selectedBuildingIds: new Set(),
  toggleBuildingSelection: (id) =>
    set((state) => {
      const next = new Set(state.selectedBuildingIds)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return { selectedBuildingIds: next }
    }),
  selectAllBuildings: (ids) => set({ selectedBuildingIds: new Set(ids) }),
  clearBuildingSelections: () => set({ selectedBuildingIds: new Set() }),
}))
