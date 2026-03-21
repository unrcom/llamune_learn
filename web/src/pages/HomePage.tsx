import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { pocsApi } from '@/api/client'
import type { Poc } from '@/types'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function HomePage() {
  const navigate = useNavigate()

  const { data: pocs = [], isError } = useQuery({
    queryKey: ['pocs'],
    queryFn: pocsApi.getPocs,
  })

  if (isError) return <p className="text-destructive">PoCの取得に失敗しました</p>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">チューニング対象</h1>
      <div className="space-y-3">
        {pocs.length === 0 && (
          <p className="text-muted-foreground text-center py-12">チューニング対象がありません</p>
        )}
        {pocs.map((poc: Poc) => (
          <Card
            key={poc.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/poc/${poc.id}/jobs`)}
          >
            <CardContent className="flex items-center justify-between py-4">
              <div>
                <p className="font-medium">{poc.name}</p>
                <p className="text-sm text-muted-foreground">
                  {poc.domain} · <code className="text-xs bg-muted px-1 rounded">{poc.app_name}</code>
                </p>
              </div>
              <div className="flex items-center gap-3">
                {poc.model_name && (
                  <Badge variant="outline">{poc.model_name}</Badge>
                )}
                <span className="text-sm text-muted-foreground">{poc.job_count} ジョブ</span>
                {poc.last_trained_at && (
                  <span className="text-xs text-muted-foreground">
                    最終訓練: {new Date(poc.last_trained_at).toLocaleDateString('ja-JP')}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
