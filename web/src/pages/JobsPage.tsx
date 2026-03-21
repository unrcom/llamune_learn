import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { jobsApi, pocsApi } from '@/api/client'
import type { TrainingJob } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const JOB_STATUS: Record<number, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  1: { label: '下書き', variant: 'outline' },
  2: { label: '実行中', variant: 'default' },
  3: { label: '完了', variant: 'secondary' },
  4: { label: 'エラー', variant: 'destructive' },
}

const TRAINING_MODE: Record<number, string> = {
  1: 'バッチ',
  2: '1件ずつ',
}

export function JobsPage() {
  const { pocId } = useParams<{ pocId: string }>()
  const navigate = useNavigate()
  const numPocId = Number(pocId)

  const { data: pocs = [] } = useQuery({
    queryKey: ['pocs'],
    queryFn: pocsApi.getPocs,
  })
  const poc = pocs.find(p => p.id === numPocId)

  const { data: jobs = [], isError } = useQuery({
    queryKey: ['jobs', numPocId],
    queryFn: () => jobsApi.getJobs(numPocId),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3">
        <div>
          <button onClick={() => navigate('/')} className="text-sm text-muted-foreground hover:text-foreground mb-1">
            ← チューニング対象一覧
          </button>
          <h1 className="text-2xl font-bold">{poc?.name ?? '...'}</h1>
          {poc && (
            <p className="text-sm text-muted-foreground mt-1">
              {poc.domain} · <code className="text-xs bg-muted px-1 rounded">{poc.app_name}</code>
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button onClick={() => navigate(`/poc/${numPocId}/jobs/new`)}>
            ＋ 新規ジョブ作成
          </Button>
          <Button variant="outline" onClick={() => navigate(`/poc/${numPocId}/models`)}>
            アダプター管理
          </Button>
        </div>
      </div>

      {isError && <p className="text-destructive">ジョブの取得に失敗しました</p>}

      <div className="space-y-3">
        {jobs.length === 0 && (
          <p className="text-muted-foreground text-center py-12">ジョブがありません。新規作成してください。</p>
        )}
        {jobs.map((job: TrainingJob) => (
          <Card
            key={job.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/poc/${numPocId}/jobs/${job.id}`)}
          >
            <CardContent className="flex items-center justify-between py-4">
              <div>
                <p className="font-medium">{job.name}</p>
                <p className="text-sm text-muted-foreground">
                  {TRAINING_MODE[job.training_mode]} · {job.log_count} 件
                  {job.finished_at && ` · ${new Date(job.finished_at).toLocaleString('ja-JP')}`}
                </p>
              </div>
              <Badge variant={JOB_STATUS[job.status]?.variant}>
                {JOB_STATUS[job.status]?.label}
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
