import { createContext, useContext } from 'react'
import { useMonkeyStatus } from '@/hooks/useMonkeyStatus'
import type { InstanceStatus } from '@/hooks/useMonkeyStatus'

interface MonkeyContextValue {
  instances: InstanceStatus[]
  connected: boolean
}

const MonkeyContext = createContext<MonkeyContextValue>({ instances: [], connected: false })

export function MonkeyProvider({ children }: { children: React.ReactNode }) {
  const { instances, connected } = useMonkeyStatus()
  return (
    <MonkeyContext.Provider value={{ instances, connected }}>
      {children}
    </MonkeyContext.Provider>
  )
}

export function useMonkey() {
  return useContext(MonkeyContext)
}
