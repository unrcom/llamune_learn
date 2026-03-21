import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi, logsApi } from '@/api/client'
import type { Log, Dataset } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const TRAINING_ROLE_LABELS: Record<number, string> = {
  1: 'correction（修正）',
  2: 'reinforcement（強化）',
  3: 'graduated（修了）',
  4: 'negative（否定例）',
  5: 'synthetic（合成）',
  6: 'boundary（境界）',
}

const EVALUATION_LABELS: Record<number, { label: string; variant: 'default' | 'secondary' | 'destructive' }> = {
  1: { label: '良い', variant: 'default' },
  2: { label: '不十分', variant: 'secondary' },
  3: { label: '間違い', variant: 'destructive' },
}

const TRAINING_MODE_LABELS: Record<number, string> = {
  1: 'バッチ（全件まとめて学習）',
  2: '1件ずつ（順番に学習）',
}

export function JobCreatePage() {
  const { pocId } = useParams<{ pocId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const numPocId = Number(pocId)

  // フォーム
  const [name, setName] = useState('')
  const [trainingMode, setTrainingMode] = useState(1)
  const [iters, setIters] = useState(100)
  const [maxSeqLength, setMaxSeqLength] = useState(2048)
  const [lossThreshold, setLossThreshold] = useState(0.1)
  const [selectedLogs, setSelectedLogs] = useState<Set<number>>(new Set())
  const [error, setError] = useState('')

  // 絞り込み
  const [filterDataset, setFilterDataset] = useState<number | ''>('')
  const [filterTrained, setFilterTrained] = useState('all')

  const { data: datasets = [] } = useQuery({
    queryKey: ['datasets', numPocId],
    queryFn: () => logsApi.getDatasets(numPocId),
  })

  const { data: logs = [] } = useQuery({
    queryKey: ['logs', numPocId, filterDataset, filterTrained],
    queryFn: () => logsApi.getLogs({
      poc_id: numPocId,
      dataset_id: filterDataset !== '' ? filterDataset : undefined,
      trained: filterTrained !== 'all' ? filterTrained : undefined,
    }),
  })

  const createMutation = useMutation({
    mutationFn: jobsApi.createJob,
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ['jobs', numPocId] })
      navigate(`/poc/${numPocId}/jobs/${job.id}`)
    },
    onError: (e: any) => setError(e.message),
  })

  function toggleLog(logId: number) {
    setSelectedLogs(prev => {
      const next = new Set(prev)
      if (next.has(logId)) next.delete(logId)
      else next.add(logId)
      return next
    })
  }

  function handleCreate() {
    if (!name.trim()) { setError('ジョブ名を入力してください'); return }
    if (selectedLogs.size === 0) { setError('訓練データを1件以上選択してください'); return }

    createMutation.mutate({
      poc_id: numPocId,
      name: name.trim(),
      training_data: Array.from(selectedLogs).map(log_id => ({ log_id, role: 1 })),
      training_mode: trainingMode,
      iters,
      max_seq_length: maxSeqLength,
      loss_threshold: lossThreshold,
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <button onClick={() => navigate(`/poc/${numPocId}/jobs`)} className="text-sm text-muted-foreground hover:text-foreground mb-1">
          ← ジョブ一覧
        </button>
        <h1 className="text-2xl font-bold">新規ジョブ作成</h1>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Card>
        <CardHeader><CardTitle>基本設定</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>ジョブ名 *</Label>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="例: 会計基礎バッチ01" className="mt-1" />
          </div>

          <div>
            <Label>訓練モード</Label>
            <div className="flex gap-4 mt-2">
              {[1, 2].map(mode => (
                <label key={mode} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value={mode}
                    checked={trainingMode === mode}
                    onChange={() => setTrainingMode(mode)}
                  />
                  <span className="text-sm">{TRAINING_MODE_LABELS[mode]}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>最大イテレーション数</Label>
              <Input
                type="number"
                value={iters}
                onChange={e => setIters(Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label>最大シーケンス長</Label>
              <Input
                type="number"
                value={maxSeqLength}
                onChange={e => setMaxSeqLength(Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label>loss閾値</Label>
              <Input
                type="number"
                step="0.01"
                value={lossThreshold}
                onChange={e => setLossThreshold(Number(e.target.value))}
                className="mt-1"
              />
            </div>
          </div>

          <div className="text-xs text-muted-foreground space-y-1 bg-muted rounded p-3">
            <p>表示のみ: learning_rate=0.00001 / num_layers=16 / batch_size=1</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>訓練データ選択</CardTitle>
            <span className="text-sm text-muted-foreground">{selectedLogs.size} 件選択中</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <div className="flex-1">
              <Label className="text-xs">データセット</Label>
              <select
                className="w-full border rounded px-3 py-2 text-sm bg-background mt-1"
                value={filterDataset}
                onChange={e => setFilterDataset(e.target.value ? Number(e.target.value) : '')}
              >
                <option value="">すべて</option>
                {datasets.map((d: Dataset) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <Label className="text-xs">訓練状況</Label>
              <select
                className="w-full border rounded px-3 py-2 text-sm bg-background mt-1"
                value={filterTrained}
                onChange={e => setFilterTrained(e.target.value)}
              >
                <option value="all">すべて</option>
                <option value="untrained">未実施のみ</option>
                <option value="trained">訓練済みのみ</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            {logs.length === 0 && (
              <p className="text-muted-foreground text-sm text-center py-6">
                訓練データがありません。poc でtraining_roleを設定してください。
              </p>
            )}
            {logs.map((log: Log) => (
              <div
                key={log.id}
                className={`border rounded p-3 cursor-pointer transition-colors ${
                  selectedLogs.has(log.id) ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                }`}
                onClick={() => toggleLog(log.id)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <input
                      type="checkbox"
                      checked={selectedLogs.has(log.id)}
                      onChange={() => {}}
                      onClick={e => { e.stopPropagation(); toggleLog(log.id) }}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <p className="text-sm">{log.question}</p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className="text-xs text-muted-foreground">
                          {TRAINING_ROLE_LABELS[log.training_role ?? 0] ?? '不明'}
                        </span>
                        {log.evaluation && (
                          <Badge variant={EVALUATION_LABELS[log.evaluation]?.variant} className="text-xs">
                            {EVALUATION_LABELS[log.evaluation]?.label}
                          </Badge>
                        )}
                        {log.username && (
                          <span className="text-xs text-muted-foreground">{log.username}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    {log.is_trained ? (
                      <div className="text-xs space-y-0.5">
                        <p className="text-green-600 font-medium">訓練済み</p>
                        {log.final_loss !== null && <p className="text-muted-foreground">loss: {log.final_loss.toFixed(4)}</p>}
                        {log.iterations !== null && <p className="text-muted-foreground">{log.iterations} iter</p>}
                        {log.job_name && <p className="text-muted-foreground">{log.job_name}</p>}
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">未実施</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={() => navigate(`/poc/${numPocId}/jobs`)}>キャンセル</Button>
        <Button onClick={handleCreate} disabled={createMutation.isPending}>
          {createMutation.isPending ? '作成中...' : '作成'}
        </Button>
      </div>
    </div>
  )
}
