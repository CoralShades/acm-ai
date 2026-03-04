import { create } from 'zustand'

interface BuildingStoreState {
  selectedBuildingId: string | null
  setSelectedBuilding: (id: string | null) => void
}

export const useBuildingStore = create<BuildingStoreState>((set) => ({
  selectedBuildingId: null,
  setSelectedBuilding: (id) => set({ selectedBuildingId: id }),
}))
