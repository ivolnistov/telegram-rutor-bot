import { useQuery } from '@tanstack/react-query'
import { downloadTorrent, getTorrents } from 'api'
import { Button } from 'components/ui/Button'
import { Input } from 'components/ui/Input'
import { useDebounce } from 'hooks/useDebounce'
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  Search,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import type { Torrent } from 'types'

const PAGE_SIZE = 30

const LibraryPage = () => {
  const { t } = useTranslation()
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(0)
  const debouncedQuery = useDebounce(searchQuery, 300)

  const { data, isLoading } = useQuery({
    queryKey: ['torrents', debouncedQuery, page],
    queryFn: () => getTorrents(PAGE_SIZE, page * PAGE_SIZE, debouncedQuery),
  })

  const torrents = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setPage(0)
  }

  return (
    <div>
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
        <h3 className="text-xl font-semibold">{t('library.title')}</h3>
        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-500">{total} torrents</span>
          <div className="w-64">
            <Input
              icon={<Search className="size-4" />}
              type="text"
              placeholder={t('library.search_placeholder')}
              value={searchQuery}
              onChange={(e) => {
                handleSearch(e.target.value)
              }}
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-zinc-500">{t('library.loading')}</div>
      ) : (
        <div className="rounded-lg border border-zinc-800 overflow-hidden bg-zinc-900/30">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-900 text-zinc-400 font-medium">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3 w-24">Size</th>
                  <th className="px-4 py-3 w-32">Date</th>
                  <th className="px-4 py-3 w-24 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {torrents.map((torrent: Torrent) => (
                  <tr
                    key={torrent.id}
                    className="group hover:bg-zinc-900/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {torrent.film?.poster ? (
                          <img
                            src={
                              torrent.film.poster.startsWith('http')
                                ? torrent.film.poster
                                : `https://image.tmdb.org/t/p/w92${torrent.film.poster}`
                            }
                            alt={torrent.film.name}
                            className="w-8 h-12 object-cover rounded bg-zinc-800"
                          />
                        ) : (
                          <div className="w-8 h-12 bg-zinc-800 rounded flex items-center justify-center text-xs text-zinc-600">
                            ?
                          </div>
                        )}
                        <div className="min-w-0">
                          <div
                            className="font-medium text-zinc-200 line-clamp-2"
                            title={torrent.name}
                          >
                            {torrent.name}
                          </div>
                          {torrent.film && (
                            <div className="text-xs text-violet-400 mt-0.5 truncate">
                              Linked: {torrent.film.name} ({torrent.film.year})
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-zinc-500 font-mono text-xs">
                      {(torrent.sz / 1024 / 1024 / 1024).toFixed(2)} GB
                    </td>
                    <td className="px-4 py-3 text-zinc-500 text-xs">
                      {new Date(torrent.created).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {torrent.downloaded ? (
                        <span className="inline-flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2.5 py-1.5 rounded-md border border-green-500/20">
                          <Check className="size-3" />
                          Downloaded
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          className="h-8 text-xs bg-zinc-800 hover:bg-zinc-700"
                          onClick={() => {
                            void (async () => {
                              try {
                                await downloadTorrent(torrent.id)
                                toast.success(t('library.download_started'))
                              } catch (e) {
                                console.error(e)
                                toast.error(t('library.download_failed'))
                              }
                            })()
                          }}
                        >
                          <Download className="size-3 mr-1.5" />
                          {t('library.download')}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {torrents.length === 0 && (
            <div className="py-12 text-center text-zinc-500 border-t border-zinc-800">
              {t('library.no_films')}
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-zinc-800 bg-zinc-900/50">
              <Button
                variant="ghost"
                size="sm"
                disabled={page === 0}
                onClick={() => {
                  setPage((p) => p - 1)
                }}
              >
                <ChevronLeft className="size-4 mr-1" />
                Prev
              </Button>
              <span className="text-xs text-zinc-500">
                {page + 1} / {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                disabled={page >= totalPages - 1}
                onClick={() => {
                  setPage((p) => p + 1)
                }}
              >
                Next
                <ChevronRight className="size-4 ml-1" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
export default LibraryPage
