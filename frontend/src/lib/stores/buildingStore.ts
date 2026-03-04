import { create } from 'zustand'

export type BuildingStreamStatus = 'extracting' | 'validating' | 'complete' | 'error'

interface BuildingStoreState {
  selectedBuildingId: string | null
  setSelectedBuilding: (id: string | null) => void
  buildingStatus: Map<string, BuildingStreamStatus>
  setBuildingStatus: (buildingId: string, status: BuildingStreamStatus) => void
  clearBuildingStatuses: () => void
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
}))
