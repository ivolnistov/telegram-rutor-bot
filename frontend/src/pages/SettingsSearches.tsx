import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createSearch,
  deleteSearch,
  executeSearch,
  getCategories,
  getMe,
  getSearches,
  updateSearch,
} from 'api'
import { Button } from 'components/ui/Button'
import { Card } from 'components/ui/Card'
import { Checkbox } from 'components/ui/Checkbox'
import { Input } from 'components/ui/Input'
import { Modal } from 'components/ui/Modal'
import { Select } from 'components/ui/Select'
import { Link } from '@tanstack/react-router'
import {
  Bell,
  BellOff,
  Clock,
  Edit2,
  ExternalLink,
  Filter,
  Play,
  Plus,
  Radar,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import type { Category, Search } from 'types'

const SearchModal = ({
  search,
  categories,
  chatId,
  onClose,
}: {
  search?: Search | null
  categories: Category[]
  chatId: number
  onClose: () => void
}) => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [url, setUrl] = useState(search?.url ?? '')
  const [cron, setCron] = useState(search?.cron ?? '0 */4 * * *')
  const [category, setCategory] = useState(search?.category ?? '')
  const [qFilters, setQFilters] = useState(search?.quality_filters ?? '')
  const [tFilters, setTFilters] = useState(search?.translation_filters ?? '')

  const isEdit = !!search

  const categoryOptions = [
    { value: '', label: t('searches.select_category') },
    ...categories.map((c) => ({
      value: c.name,
      label: `${c.icon ?? ''} ${c.name}`.trim(),
    })),
  ]

  const createMut = useMutation({
    mutationFn: createSearch,
    onSuccess: async () => {
      toast.success(t('searches.messages.created'))
      await queryClient.invalidateQueries({ queryKey: ['searches'] })
      onClose()
    },
    onError: () => {
      toast.error(t('searches.messages.failed_create'))
    },
  })

  const updateMut = useMutation({
    mutationFn: updateSearch,
    onSuccess: async () => {
      toast.success(t('common.saved'))
      await queryClient.invalidateQueries({ queryKey: ['searches'] })
      onClose()
    },
    onError: () => {
      toast.error(t('common.error'))
    },
  })

  const handleSubmit = () => {
    if (!url.trim()) {
      toast.error(t('searches.validation.url_required'))
      return
    }
    if (!category) {
      toast.error(t('searches.validation.category_required'))
      return
    }

    if (isEdit) {
      updateMut.mutate({
        id: search.id,
        url: url.trim(),
        cron,
        category,
        quality_filters: qFilters || null,
        translation_filters: tFilters || null,
      })
    } else {
      const fd = new FormData()
      fd.append('url', url.trim())
      fd.append('cron', cron)
      fd.append('category', category)
      fd.append('chat_id', String(chatId))
      if (qFilters) fd.append('quality_filters', qFilters)
      if (tFilters) fd.append('translation_filters', tFilters)
      createMut.mutate(fd)
    }
  }

  const isLoading = createMut.isPending || updateMut.isPending

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={
        isEdit
          ? t('searches.edit_title', { id: search.id })
          : t('searches.create_title')
      }
    >
      <div className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">
            {t('searches.url')}
          </label>
          <Input
            value={url}
            onChange={(e) => {
              setUrl(e.target.value)
            }}
            className="text-zinc-200"
            placeholder={t('searches.url_placeholder')}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">
            {t('searches.category_label')}
          </label>
          <Select
            value={category}
            onChange={(v) => {
              setCategory(String(v))
            }}
            options={categoryOptions}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">
            {t('searches.cron_label')}
          </label>
          <Input
            value={cron}
            onChange={(e) => {
              setCron(e.target.value)
            }}
            className="text-zinc-200 font-mono"
            placeholder="0 */4 * * *"
          />
        </div>
        <div className="border-t border-zinc-800 pt-4 mt-4 space-y-3">
          <p className="text-xs font-medium text-zinc-400 flex items-center gap-1.5">
            <Filter className="size-3.5" />
            {t('settings.search_filters')}
          </p>
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">
              {t('searches.quality_filters_label', 'Quality Filters')}
            </label>
            <Input
              value={qFilters}
              onChange={(e) => {
                setQFilters(e.target.value)
              }}
              className="text-zinc-200"
              placeholder="e.g. 1080p, 2160p, HDR"
            />
            <p className="text-[10px] text-zinc-600 mt-0.5">
              {t('searches.filters_hint', 'Leave empty to use global filters')}
            </p>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">
              {t('searches.translation_filters_label', 'Translation Filters')}
            </label>
            <Input
              value={tFilters}
              onChange={(e) => {
                setTFilters(e.target.value)
              }}
              className="text-zinc-200"
              placeholder="e.g. Dubbed, MVO, Original"
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-zinc-800">
          <Button variant="ghost" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleSubmit} isLoading={isLoading}>
            {t('common.save')}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

const SettingsSearches = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [notifyMap, setNotifyMap] = useState<Record<number, boolean>>({})
  const [editingSearch, setEditingSearch] = useState<Search | null>(null)
  const [isCreating, setIsCreating] = useState(false)
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
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex gap-2 mb-8 border-b border-zinc-800">
        <Link
          to="/settings/category"
          className="px-4 py-2 text-sm font-medium text-zinc-500 hover:text-zinc-300 border-b-2 border-transparent hover:border-zinc-800 transition-colors"
        >
          {t('sidebar.categories')}
        </Link>
        <Link
          to="/settings/users"
          className="px-4 py-2 text-sm font-medium text-zinc-500 hover:text-zinc-300 border-b-2 border-transparent hover:border-zinc-800 transition-colors"
        >
          {t('sidebar.users')}
        </Link>
        <Link
          to="/settings/config"
          className="px-4 py-2 text-sm font-medium text-zinc-500 hover:text-zinc-300 border-b-2 border-transparent hover:border-zinc-800 transition-colors"
        >
          {t('settings.title')}
        </Link>
        <Link
          to="/settings/searches"
          className="px-4 py-2 text-sm font-medium border-b-2 border-violet-500 text-violet-400"
        >
          {t('sidebar.searches')}
        </Link>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold flex items-center gap-3">
          <Radar className="size-5 text-violet-400" />
          {t('searches.title')}
        </h3>

        <div className="flex items-center gap-3">
          <Select
            value={categoryFilter}
            onChange={(v) => {
              setCategoryFilter(String(v))
            }}
            options={categoryOptions}
            className="w-48"
          />
          <Button
            onClick={() => {
              setIsCreating(true)
            }}
          >
            <Plus className="size-4 mr-2" />
            {t('searches.add')}
          </Button>
        </div>
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
                    {t('searches.last_run')}:{' '}
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
                    ? t('searches.notify_on')
                    : t('searches.notify_off')
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
                {t('searches.run_now')}
              </Button>

              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  setEditingSearch(search)
                }}
              >
                <Edit2 className="size-4 text-zinc-500 hover:text-zinc-300" />
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

      {(isCreating || editingSearch) && (
        <SearchModal
          search={editingSearch}
          categories={categories ?? []}
          chatId={user?.chat_id ?? 0}
          onClose={() => {
            setIsCreating(false)
            setEditingSearch(null)
          }}
        />
      )}
    </div>
  )
}

export default SettingsSearches
