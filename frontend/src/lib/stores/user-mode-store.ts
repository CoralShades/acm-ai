import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type UserMode = 'standard' | 'admin'

interface UserModeStore {
  mode: UserMode
  setMode: (mode: UserMode) => void
}

export const useUserModeStore = create<UserModeStore>()(
  persist(
    (set) => ({
      mode: 'standard',
      setMode: (mode) => set({ mode }),
    }),
    {
      name: 'acm-user-mode',
    }
  )
)
