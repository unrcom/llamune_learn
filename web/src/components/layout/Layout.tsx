import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { clearTokens } from '@/api/client'
import { useMonkeyStatus } from '@/hooks/useMonkeyStatus'

interface Props {
  children: React.ReactNode
  onLogout: () => void
}

const STATUS_LABEL: Record<string, string> = {
  idle: 'アイドル',
  training: '訓練中',
}

const STATUS_COLOR: Record<string, string> = {
  idle: 'bg-green-100 text-green-800',
  training: 'bg-blue-100 text-blue-800',
}

export function Layout({ children, onLogout }: Props) {
  const navigate = useNavigate()
  const { instances, connected } = useMonkeyStatus()

  function handleLogout() {
    clearTokens()
    onLogout()
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 bg-background border-b">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <button
              onClick={() => navigate('/')}
              className="font-bold text-lg tracking-tight shrink-0 hover:opacity-80"
            >
              llamune <span className="text-muted-foreground font-normal text-sm">learn</span>
            </button>
            {connected && instances.length > 0 && (
              <div className="flex items-center gap-1 overflow-x-auto">
                {instances.map(i => {
                  const statusColor = i.healthy
                    ? STATUS_COLOR[i.model_status] ?? 'bg-gray-100 text-gray-800'
                    : 'bg-red-100 text-red-800'
                  const statusLabel = i.healthy
                    ? STATUS_LABEL[i.model_status] ?? i.model_status
                    : '応答なし'
                  return (
                    <span
                      key={i.instance_id}
                      title={i.instance_id}
                      className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap shrink-0 ${statusColor}`}
                    >
                      {i.display_name}: {statusLabel}
                      {i.healthy && i.model_status === 'training' && i.current_model && ` [${i.current_model}]`}
                    </span>
                  )
                })}
              </div>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout} className="text-muted-foreground">
            ログアウト
          </Button>
        </div>
      </header>
      <Separator />
      <main className="max-w-5xl mx-auto px-6 py-6">
        {children}
      </main>
    </div>
  )
}
