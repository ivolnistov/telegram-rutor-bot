import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  deleteSearch,
  executeSearch,
  getCategories,
  getMe,
  getSearches,
} from 'api'
import { Button } from 'components/ui/Button'
import { Card } from 'components/ui/Card'
import { Checkbox } from 'components/ui/Checkbox'
import { Select } from 'components/ui/Select'
import {
  Bell,
  BellOff,
  Clock,
  ExternalLink,
  Play,
  Radar,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import type { Category, Search } from 'types'

const Searches = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [notifyMap, setNotifyMap] = useState<Record<number, boolean>>({})

  const { data: searches, isLoading } = useQuery({
    queryKey: ['searches'],
    queryFn: getSearches,
    refetchInterval: 10000,
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
    staleTime: 1000 * 60 * 5,
  })

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    staleTime: 1000 * 60 * 10,
  })

  const executeMutation = useMutation({
    mutationFn: ({ id, notify }: { id: number; notify: boolean }) =>
      executeSearch(id, user?.chat_id ?? 0, notify),
    onSuccess: () => {
      toast.success(t('searches.messages.task_started'))
      void queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: () => {
      toast.error(t('searches.messages.failed_task'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSearch(id),
    onSuccess: () => {
      toast.success(t('searches.messages.deleted'))
      void queryClient.invalidateQueries({ queryKey: ['searches'] })
    },
  })

  const getNotify = (id: number) => notifyMap[id] ?? true

  const toggleNotify = (id: number) => {
    setNotifyMap((prev) => ({ ...prev, [id]: !(prev[id] ?? true) }))
  }

  const categoryOptions = [
    { value: 'all', label: t('searches.all_categories') },
    ...(categories?.map((c: Category) => ({
      value: c.name,
      label: `${c.icon ?? ''} ${c.name}`.trim(),
    })) ?? []),
  ]

  const filtered =
    categoryFilter === 'all'
      ? searches
      : searches?.filter((s: Search) => s.category === categoryFilter)

  if (isLoading)
    return <div className="text-zinc-500">{t('common.loading')}</div>

  return (
    <div className="mb-16">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold flex items-center gap-3">
          <Radar className="size-5 text-zinc-400" />
          {t('searches.title')}
        </h3>

        <Select
          value={categoryFilter}
          onChange={(v) => {
            setCategoryFilter(String(v))
          }}
          options={categoryOptions}
          className="w-48"
        />
      </div>

      <div className="space-y-3">
        {filtered?.map((search: Search) => (
          <Card
            key={search.id}
            className="flex items-center justify-between py-3 px-4"
          >
            <div className="flex-1 min-w-0 mr-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-zinc-200 truncate">
                  {search.query ?? search.url}
                </span>
                <a
                  href={search.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-500 hover:text-zinc-300 transition-colors shrink-0"
                >
                  <ExternalLink className="size-3.5" />
                </a>
              </div>
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                {search.category && (
                  <span className="bg-zinc-800 px-2 py-0.5 rounded text-zinc-400">
                    {search.category}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Clock className="size-3" />
                  {search.cron}
                </span>
                {search.last_success && (
                  <span>
                    {t('searches.last_run', 'Last run')}:{' '}
                    {new Date(search.last_success).toLocaleString()}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => {
                  toggleNotify(search.id)
                }}
                className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs transition-colors hover:bg-zinc-800"
                title={
                  getNotify(search.id)
                    ? t('searches.notify_on', 'Notifications on')
                    : t('searches.notify_off', 'Notifications off')
                }
              >
                <Checkbox
                  checked={getNotify(search.id)}
                  onCheckedChange={() => {
                    toggleNotify(search.id)
                  }}
                />
                {getNotify(search.id) ? (
                  <Bell className="size-3.5 text-violet-400" />
                ) : (
                  <BellOff className="size-3.5 text-zinc-500" />
                )}
              </button>

              <Button
                variant="primary"
                size="sm"
                isLoading={
                  executeMutation.isPending &&
                  executeMutation.variables.id === search.id
                }
                onClick={() => {
                  executeMutation.mutate({
                    id: search.id,
                    notify: getNotify(search.id),
                  })
                }}
              >
                <Play className="size-3.5" />
                {t('searches.run_now', 'Run Now')}
              </Button>

              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  if (confirm(t('searches.delete_confirm_title'))) {
                    deleteMutation.mutate(search.id)
                  }
                }}
              >
                <Trash2 className="size-4 text-zinc-500 hover:text-red-400" />
              </Button>
            </div>
          </Card>
        ))}

        {(!filtered || filtered.length === 0) && (
          <div className="py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
            {t('searches.no_searches')}
          </div>
        )}
      </div>
    </div>
  )
}

export default Searches
