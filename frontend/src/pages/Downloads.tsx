import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getDownloads, deleteDownload } from 'api'
import { Card } from 'components/ui/Card'
import {
  Download as DownloadIcon,
  ArrowDown,
  ArrowUp,
  Loader2,
  Trash,
} from 'lucide-react'
import type { Download } from 'types'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'

const Downloads = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const { data: downloads, isLoading } = useQuery({
    queryKey: ['downloads'],
    queryFn: getDownloads,
    refetchInterval: 3000,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDownload,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['downloads'] })
      toast.success(t('downloads.deleted'))
    },
    onError: () => {
      toast.error(t('downloads.delete_failed'))
    },
  })

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${String(parseFloat((bytes / Math.pow(k, i)).toFixed(2)))} ${sizes[i]}`
  }

  const formatSpeed = (bytesPerSec: number) => {
    return formatSize(bytesPerSec) + '/s'
  }

  const getStatusColor = (status: string) => {
    if (status.includes('downloading')) return 'text-blue-400'
    if (status.includes('uploading') || status.includes('seeding'))
      return 'text-emerald-400'
    if (status.includes('paused')) return 'text-yellow-400'
    return 'text-zinc-500'
  }

  if (isLoading)
    return (
      <div className="text-zinc-500 flex items-center gap-2">
        <Loader2 className="animate-spin size-4" /> {t('common.loading')}
      </div>
    )

  return (
    <div className="mb-16">
      <h3 className="text-xl font-semibold flex items-center gap-3 mb-6">
        <DownloadIcon className="size-5 text-zinc-400" />
        {t('downloads.title', 'Downloads')}
      </h3>

      <div className="space-y-3">
        {downloads?.map((download: Download) => (
          <Card key={download.hash} className="py-4 px-5 group relative">
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-4">
                <span
                  className="font-medium truncate text-zinc-200"
                  title={download.name}
                >
                  {download.name}
                </span>
                <div className="flex items-center gap-3 shrink-0">
                  <span
                    className={`text-xs uppercase font-bold tracking-wider ${getStatusColor(download.status)}`}
                  >
                    {download.status}
                  </span>
                  <button
                    onClick={() => {
                      deleteMutation.mutate(download.hash)
                    }}
                    disabled={deleteMutation.isPending}
                    className="text-zinc-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all p-1"
                    title={t('downloads.delete')}
                  >
                    <Trash className="size-4" />
                  </button>
                </div>
              </div>

              <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${download.status.includes('paused') ? 'bg-zinc-600' : 'bg-blue-500'}`}
                  style={{ width: `${String(download.progress)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-zinc-500 font-mono">
                <div className="flex items-center gap-4">
                  <span>{formatSize(download.size)}</span>
                  <span>{download.progress.toFixed(1)}%</span>
                  {download.seeds !== undefined && (
                    <span className="text-zinc-400">
                      S: {download.seeds} / P: {download.peers}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1 text-emerald-500/80">
                    <ArrowDown className="size-3" />
                    {formatSpeed(download.download_rate)}
                  </span>
                  <span className="flex items-center gap-1 text-blue-500/80">
                    <ArrowUp className="size-3" />
                    {formatSpeed(download.upload_rate)}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        ))}

        {downloads?.length === 0 && (
          <div className="py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
            {t('downloads.no_downloads', 'No active downloads')}
          </div>
        )}
      </div>
    </div>
  )
}

export default Downloads
