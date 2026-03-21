import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/api/client'
import { useMonkeyStatus } from '@/hooks/useMonkeyStatus'
import type { TrainingJob } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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

export function JobDetailPage() {
  const { pocId, jobId } = useParams<{ pocId: string; jobId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const numPocId = Number(pocId)
  const numJobId = Number(jobId)

  const { instances } = useMonkeyStatus()
  const learnInstance = instances.find(i => i.instance_id.startsWith('llamune-learn'))

  const { data: job, isError } = useQuery({
    queryKey: ['job', numJobId],
    queryFn: () => jobsApi.getJob(numJobId),
  })

  const executeMutation = useMutation({
    mutationFn: () => jobsApi.executeJob(numJobId),
    onSuccess: (updated) => {
      qc.setQueryData(['job', numJobId], updated)
      qc.invalidateQueries({ queryKey: ['jobs', numPocId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => jobsApi.deleteJob(numJobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs', numPocId] })
      navigate(`/poc/${numPocId}/jobs`)
    },
  })

  if (isError) return <p className="text-destructive">ジョブの取得に失敗しました</p>
  if (!job) return <p className="text-muted-foreground">読み込み中...</p>

  return (
    <div className="space-y-6">
      {learnInstance && learnInstance.model_status === 'training' && (
        <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded flex items-center gap-2">
          <span className="animate-pulse">●</span>
          <span>訓練中: {learnInstance.current_model}</span>
        </div>
      )}
      <div>
        <button onClick={() => navigate(`/poc/${numPocId}/jobs`)} className="text-sm text-muted-foreground hover:text-foreground mb-1">
          ← ジョブ一覧
        </button>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">{job.name}</h1>
          <Badge variant={JOB_STATUS[job.status]?.variant}>
            {JOB_STATUS[job.status]?.label}
          </Badge>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>ジョブ情報</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div><span className="text-muted-foreground">訓練モード</span><p>{TRAINING_MODE[job.training_mode]}</p></div>
            <div><span className="text-muted-foreground">データ件数</span><p>{job.log_count} 件</p></div>
            <div><span className="text-muted-foreground">最大イテレーション</span><p>{job.iters}</p></div>
            <div><span className="text-muted-foreground">loss閾値</span><p>{job.loss_threshold ?? '未設定'}</p></div>
            <div><span className="text-muted-foreground">最大シーケンス長</span><p>{job.max_seq_length}</p></div>
            <div><span className="text-muted-foreground">インスタンス</span><p>{job.instance_id ?? '-'}</p></div>
            {job.started_at && <div><span className="text-muted-foreground">開始</span><p>{new Date(job.started_at).toLocaleString('ja-JP')}</p></div>}
            {job.finished_at && <div><span className="text-muted-foreground">終了</span><p>{new Date(job.finished_at).toLocaleString('ja-JP')}</p></div>}
            {job.output_model_name && <div className="col-span-2"><span className="text-muted-foreground">出力モデル</span><p className="font-mono text-xs">{job.output_model_name}</p></div>}
            {job.error_message && <div className="col-span-2"><span className="text-destructive">エラー</span><p className="text-destructive">{job.error_message}</p></div>}
          </div>
          <div className="text-xs text-muted-foreground bg-muted rounded p-2 mt-2">
            learning_rate={job.learning_rate} / num_layers={job.num_layers} / batch_size={job.batch_size}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        {(job.status === 1 || job.status === 4) && (
          <Button onClick={() => executeMutation.mutate()} disabled={executeMutation.isPending}>
            {executeMutation.isPending ? '実行中...' : '実行'}
          </Button>
        )}
        {job.status !== 2 && (
          <Button
            variant="destructive"
            onClick={() => { if (confirm('削除しますか？')) deleteMutation.mutate() }}
            disabled={deleteMutation.isPending}
          >
            削除
          </Button>
        )}
      </div>
    </div>
  )
}
