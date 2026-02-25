import { useQuery } from '@tanstack/react-query'
import { getTasks } from 'api'
import { Card } from 'components/ui/Card'
import { Clock } from 'lucide-react'
import type { TaskExecution } from 'types'
import { useTranslation } from 'react-i18next'

const Tasks = () => {
  const { t, i18n } = useTranslation()
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => getTasks(50),
    refetchInterval: 5000,
  })

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString(i18n.language)
  }

  const getDuration = (start: string, end?: string | null) => {
    if (!end) return t('tasks.running')
    const diff = new Date(end).getTime() - new Date(start).getTime()
    return `${(diff / 1000).toFixed(1)}s`
  }

  if (isLoading)
    return <div className="text-zinc-500">{t('common.loading')}</div>

  return (
    <div className="mb-16">
      <h3 className="text-xl font-semibold flex items-center gap-3 mb-6">
        <Clock className="size-5 text-zinc-400" />
        {t('tasks.title')}
      </h3>

      <div className="space-y-3">
        {tasks?.map((task: TaskExecution) => (
          <Card
            key={task.id}
            className="flex items-center justify-between py-3 px-4"
          >
            <div className="flex items-center gap-4">
              <div className="flex flex-col">
                <span
                  className={`text-sm font-medium ${
                    task.status === 'success'
                      ? 'text-zinc-200'
                      : task.status === 'failed'
                        ? 'text-red-400'
                        : task.status === 'pending'
                          ? 'text-zinc-500'
                          : 'text-blue-400'
                  }`}
                >
                  {t('tasks.search_id', { id: task.search_id })}
                </span>
                <span className="text-xs text-zinc-500">
                  {formatDate(task.start_time)}
                </span>
              </div>
            </div>

            <div className="flex flex-col items-end gap-1 min-w-[200px]">
              {/* Status and Result */}
              <div className="flex items-center gap-2">
                <span
                  className={`size-2.5  rounded-full ${
                    task.status === 'pending'
                      ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.5)]'
                      : task.status === 'running'
                        ? 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)] animate-pulse'
                        : task.status === 'success'
                          ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                          : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
                  }`}
                />
                <span
                  className={`text-xs font-medium ${
                    task.status === 'pending'
                      ? 'text-yellow-500'
                      : task.status === 'running'
                        ? 'text-blue-500'
                        : task.status === 'success'
                          ? 'text-emerald-500'
                          : 'text-red-500'
                  }`}
                >
                  {task.status === 'pending'
                    ? t('tasks.pending')
                    : task.status === 'running'
                      ? t('tasks.running')
                      : task.status === 'success'
                        ? t('tasks.success')
                        : t('tasks.failed')}
                </span>
              </div>

              {/* Result Details */}
              {(task.result || task.status === 'running') && (
                <div className="text-xs text-zinc-400 font-mono mt-1 text-right">
                  {task.status === 'running' ? (
                    <div className="flex items-center justify-end gap-2">
                      <span>{task.progress}%</span>
                      <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all duration-500"
                          style={{ width: `${String(task.progress)}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <div
                      dangerouslySetInnerHTML={{ __html: task.result || '' }}
                    />
                  )}
                </div>
              )}

              <div className="text-[10px] text-zinc-600 font-mono mt-1">
                {t('tasks.duration')}:{' '}
                {getDuration(task.start_time, task.end_time)} • ID: {task.id}
              </div>
            </div>
          </Card>
        ))}

        {tasks?.length === 0 && (
          <div className="py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
            {t('tasks.no_tasks')}
          </div>
        )}
      </div>
    </div>
  )
}

export default Tasks
