import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addToWatchlist,
  createSearch,
  deleteRating,
  downloadTorrent,
  getLibrary,
  getMe,
  getMediaAccountStates,
  getMediaDetails,
  getMediaTorrents,
  getPersonalRecommendations,
  getRatedMedia,
  getRecommendations,
  getTrending,
  rateMedia,
  searchDiscovery,
  searchOnRutor,
  syncLibrary,
} from 'api'
import axios from 'axios'
import { Button } from 'components/ui/Button'
import { Modal } from 'components/ui/Modal'
import { useDebounce } from 'hooks/useDebounce'
import {
  Check,
  Download,
  Eye,
  Loader2,
  RefreshCw,
  Rss,
  Search,
  Star,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import type { TmdbMedia } from 'types'
// ... imports

const MediaModal = ({
  media,
  onClose,
}: {
  media: TmdbMedia
  onClose: () => void
}) => {
  const { t } = useTranslation()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const queryClient = useQueryClient()

  const [isSearchingLive, setIsSearchingLive] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [torrentSearch, setTorrentSearch] = useState('')
  const [isTorrentsExpanded, setIsTorrentsExpanded] = useState(false)

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>
    if (isPolling) {
      timeout = setTimeout(() => {
        setIsPolling(false)
      }, 30000)
    }
    return () => {
      clearTimeout(timeout)
    }
  }, [isPolling])

  const handleSearchOnRutor = async () => {
    setIsSearchingLive(true)
    setIsPolling(true)
    try {
      // Use new endpoint that handles TMDB ID
      const { status } = await searchOnRutor(media.media_type, media.id)
      if (status === 'search_started') {
        toast.success(t('library.search_started'))
      } else {
        toast.success(t('success'))
      }
    } catch (e: unknown) {
      let message = t('error')
      if (axios.isAxiosError(e)) {
        message =
          (e.response?.data as { detail?: string } | undefined)?.detail ||
          e.message
      } else if (e instanceof Error) {
        message = e.message
      }
      toast.error(message)
    } finally {
      setIsSearchingLive(false)
    }
  }

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    staleTime: Infinity,
  })

  const handleSubscribe = async () => {
    if (!user) {
      toast.error(t('error'))
      return
    }

    setIsSubmitting(true)
    try {
      let title =
        media.title ||
        media.name ||
        media.original_title ||
        media.original_name ||
        ''

      const releaseDate = media.release_date || media.first_air_date
      if (releaseDate) {
        const year = releaseDate.split('-')[0]
        if (year) {
          title += ` ${year}`
        }
      }

      const url = `https://rutor.info/search/0/0/0/0/${encodeURIComponent(title || '')}`
      const cron = '0 */4 * * *' // Every 4 hours

      const formData = new FormData()
      formData.append('url', url)
      formData.append('cron', cron)
      formData.append('category', 'Films')
      formData.append('chat_id', String(user.chat_id))

      await createSearch(formData)
      toast.success(t('discovery.subscribed') || 'Subscribed successfully')
    } catch {
      toast.error(t('error'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', media.id],
    queryFn: () => getRecommendations(media.title ? 'movie' : 'tv', media.id),
    enabled: !!media.id,
  })

  const { data: accountStates } = useQuery({
    queryKey: ['accountStates', media.id],
    queryFn: () =>
      getMediaAccountStates(media.title ? 'movie' : 'tv', media.id),
    enabled: !!media.id,
  })

  const { data: linkedTorrents } = useQuery({
    queryKey: ['mediaTorrents', media.title ? 'movie' : 'tv', media.id],
    queryFn: () => getMediaTorrents(media.title ? 'movie' : 'tv', media.id),
    enabled: !!media.id,
    refetchInterval: isPolling ? 2000 : false,
  })

  const { data: fullMedia } = useQuery({
    queryKey: ['media', media.media_type, media.id],
    queryFn: () => getMediaDetails(media.media_type, media.id),
    enabled: !!media.id,
    staleTime: 1000 * 60 * 30, // 30 mins
  })

  const displayMedia = fullMedia || media

  const getYear = (date?: string) => date?.split('-')[0] || ''
  const formatRuntime = (mins?: number) => {
    if (!mins) return ''
    const h = Math.floor(mins / 60)
    const m = mins % 60
    return `${String(h)}h ${String(m)}m`
  }

  useEffect(() => {
    if (linkedTorrents && linkedTorrents.length > 0 && isPolling) {
      setIsPolling(false)
      void queryClient.invalidateQueries({ queryKey: ['discovery'] })
    }
  }, [linkedTorrents, isPolling, queryClient])
  const userRating =
    accountStates?.rated && typeof accountStates.rated !== 'boolean'
      ? accountStates.rated.value
      : 0

  const inLibrary = accountStates?.in_library
  const inWatchlist = accountStates?.watchlist

  const handleWatchlist = async () => {
    try {
      await addToWatchlist(media.title ? 'movie' : 'tv', media.id, !inWatchlist)
      toast.success(
        inWatchlist ? 'Removed from Watchlist' : 'Added to Watchlist',
      )
      await queryClient.invalidateQueries({
        queryKey: ['accountStates', media.id],
      })
      // Invalidate discovery to update watchlist feed if implemented/visible
    } catch {
      toast.error(t('error'))
    }
  }

  const handleRate = async (value: number) => {
    try {
      if (value === userRating) {
        await deleteRating(media.title ? 'movie' : 'tv', media.id)
        toast.success(t('discovery.rating_removed') || 'Rating removed')
      } else {
        await rateMedia(media.title ? 'movie' : 'tv', media.id, value)
        toast.success(t('discovery.rated') || 'Rated successfully')
      }
      await queryClient.invalidateQueries({
        queryKey: ['accountStates', media.id],
      })
      await queryClient.invalidateQueries({ queryKey: ['discovery', 'rated'] })
    } catch {
      toast.error(t('error'))
    }
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={displayMedia.title || displayMedia.name || 'Unknown'}
    >
      <div className="space-y-5">
        <div className="aspect-video w-full rounded-lg overflow-hidden bg-black/20 relative">
          <img
            src={`https://image.tmdb.org/t/p/w780${media.backdrop_path || media.poster_path || ''}`}
            alt={media.title || media.name}
            className="size-full  object-cover"
          />
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-400">
                <Star className="size-4 fill-amber-400" />
                <span className="font-bold">
                  {media.vote_average.toFixed(1)}
                </span>
              </div>
              {inLibrary && (
                <div className="flex items-center gap-1 bg-green-500/20 text-green-400 px-2 py-0.5 rounded text-xs font-medium border border-green-500/20">
                  <Check className="size-3" />
                  In Library
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-zinc-400">
            {displayMedia.release_date || displayMedia.first_air_date ? (
              <span className="text-zinc-200 font-medium">
                {getYear(
                  displayMedia.release_date || displayMedia.first_air_date,
                )}
              </span>
            ) : null}

            {displayMedia.runtime ? (
              <span>{formatRuntime(displayMedia.runtime)}</span>
            ) : null}

            {displayMedia.production_countries &&
              displayMedia.production_countries.length > 0 && (
                <div className="flex items-center gap-1.5 ml-1">
                  {displayMedia.production_countries.map((c) => {
                    const flag = c.iso_3166_1
                      ? c.iso_3166_1.toUpperCase().replaceAll(/./g, (char) => {
                          const codePoint = char.codePointAt(0)
                          return codePoint
                            ? String.fromCodePoint(127397 + codePoint)
                            : ''
                        })
                      : ''
                    return (
                      <span
                        key={c.iso_3166_1 || c.name}
                        title={c.name}
                        className="cursor-help text-base leading-none select-none opacity-80 hover:opacity-100 transition-opacity"
                      >
                        {flag}
                      </span>
                    )
                  })}
                </div>
              )}
          </div>

          {displayMedia.genres && displayMedia.genres.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {displayMedia.genres.map((g) => (
                <span
                  key={g.id}
                  className="px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 text-xs border border-zinc-700"
                >
                  {g.name}
                </span>
              ))}
            </div>
          )}

          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-1.5" title="TMDB Rating">
              <Star className="size-4 fill-amber-400 text-amber-400" />
              <span className="font-bold text-zinc-100">
                {displayMedia.vote_average.toFixed(1)}
              </span>
              <span className="text-zinc-500">TMDB</span>
            </div>

            {displayMedia.external_ids?.imdb_id && (
              <a
                href={`https://www.imdb.com/title/${displayMedia.external_ids.imdb_id}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 text-zinc-400 hover:text-[#f5c518] transition-colors"
              >
                <div className="font-bold bg-[#f5c518] text-black px-1 rounded-[2px] text-[10px] leading-none py-0.5">
                  IMDb
                </div>
                <span>View</span>
              </a>
            )}

            <a
              href={`https://www.kinopoisk.ru/index.php?kp_query=${encodeURIComponent(
                displayMedia.title || displayMedia.name || '',
              )}`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-zinc-400 hover:text-[#ff5500] transition-colors"
            >
              <div className="font-bold bg-[#ff5500] text-white px-1 rounded-[2px] text-[10px] leading-none py-0.5">
                KP
              </div>
              <span
                className={
                  displayMedia.kp_rating ? 'font-bold text-[#ff5500]' : ''
                }
              >
                {displayMedia.kp_rating
                  ? displayMedia.kp_rating.toFixed(1)
                  : 'Search'}
              </span>
            </a>
          </div>

          <p className="text-zinc-300 text-sm leading-relaxed">
            {displayMedia.overview || t('discovery.no_overview')}
          </p>
        </div>

        {/* Rating Section */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-zinc-400">
            {t('discovery.your_rating')}
          </h4>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((star) => (
              <button
                key={star}
                onClick={() => {
                  void handleRate(star)
                }}
                className="group focus:outline-none"
              >
                <Star
                  className={`size-5 transition-colors ${
                    userRating >= star
                      ? 'fill-amber-400 text-amber-400'
                      : 'text-zinc-700 hover:text-amber-400 hover:fill-amber-400'
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-zinc-800">
          <Button variant="ghost" onClick={onClose}>
            {t('common.close')}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              void handleWatchlist()
            }}
          >
            {inWatchlist ? (
              <>
                <Check className="size-4 mr-2" />
                In Watchlist
              </>
            ) : (
              <>
                <Eye className="size-4 mr-2" />
                Add to Watchlist
              </>
            )}
          </Button>
          <Button
            onClick={() => {
              void handleSubscribe()
            }}
            disabled={isSubmitting || !user}
          >
            {isSubmitting ? (
              <Loader2 className="size-4 mr-2 animate-spin" />
            ) : (
              <Rss className="size-4 mr-2" />
            )}
            {t('discovery.subscribe') || 'Subscribe'}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              void handleSearchOnRutor()
            }}
            disabled={isSearchingLive}
          >
            {isSearchingLive ? (
              <Loader2 className="size-4 mr-2 animate-spin" />
            ) : (
              <Search className="size-4 mr-2" />
            )}
            {t('discovery.search_on_rutor')}
          </Button>
        </div>

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-zinc-800">
            <h4 className="text-sm font-medium text-zinc-400">
              {t('discovery.recommendations')}
            </h4>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
              {recommendations.slice(0, 4).map((rec) => (
                <button
                  key={rec.id}
                  type="button"
                  className="aspect-[2/3] bg-zinc-800 rounded overflow-hidden relative group cursor-pointer border-none p-0"
                  title={rec.title || rec.name}
                  onClick={() => {
                    // Logic to switch modal content would be needed here,
                    // but for now simplistic approach (recursive modal or replace state)
                    // Ideally we just close and open new one, but onClose is passed from parent.
                    // Let's just ignore click or implement proper nav.
                  }}
                >
                  <img
                    src={`https://image.tmdb.org/t/p/w300${rec.poster_path || ''}`}
                    alt={rec.title || rec.name}
                    className="size-full  object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                  />
                  {rec.in_library && (
                    <div className="absolute top-1 right-1 bg-green-500/90 text-white p-0.5 rounded-full shadow-sm">
                      <Check className="size-2.5" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Linked Torrents */}
        {linkedTorrents && linkedTorrents.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-zinc-800">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-zinc-400">
                Linked Torrents ({linkedTorrents.length})
              </h4>
              {linkedTorrents.length > 4 && (
                <div className="relative w-48">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-zinc-500" />
                  <input
                    type="text"
                    value={torrentSearch}
                    onChange={(e) => {
                      setTorrentSearch(e.target.value)
                    }}
                    placeholder="Filter..."
                    className="w-full bg-zinc-900 border border-zinc-700 text-zinc-200 rounded px-2 pl-7 py-1 text-xs focus:outline-none focus:border-violet-500"
                  />
                </div>
              )}
            </div>

            <div
              className={`space-y-2 ${
                isTorrentsExpanded || torrentSearch
                  ? 'max-h-60 overflow-y-auto custom-scrollbar pr-1'
                  : ''
              }`}
            >
              {linkedTorrents
                .filter((t) =>
                  torrentSearch
                    ? t.name.toLowerCase().includes(torrentSearch.toLowerCase())
                    : true,
                )
                .slice(
                  0,
                  !isTorrentsExpanded && !torrentSearch
                    ? 4
                    : linkedTorrents.length,
                )
                .map((torrent) => (
                  <div
                    key={torrent.id}
                    className="flex items-center justify-between p-2 rounded bg-zinc-800/50 border border-zinc-700/50"
                  >
                    <div className="flex-1 min-w-0 mr-4">
                      <div
                        className="text-sm font-medium text-zinc-200 truncate"
                        title={torrent.name}
                      >
                        {torrent.name}
                      </div>
                      <div className="text-xs text-zinc-500 mt-0.5">
                        {(torrent.sz / 1024 / 1024 / 1024).toFixed(2)} GB •{' '}
                        {new Date(torrent.created).toLocaleDateString()}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      className="h-7 text-xs"
                      onClick={() => {
                        void (async () => {
                          try {
                            await downloadTorrent(torrent.id)
                            toast.success(t('library.download_started'))
                          } catch {
                            toast.error(t('library.download_failed'))
                          }
                        })()
                      }}
                    >
                      <Check className="size-3 mr-1.5" />
                      Download
                    </Button>
                  </div>
                ))}
              {linkedTorrents.filter((t) =>
                torrentSearch
                  ? t.name.toLowerCase().includes(torrentSearch.toLowerCase())
                  : true,
              ).length === 0 && (
                <div className="text-center text-zinc-500 text-sm py-2">
                  No torrents found
                </div>
              )}
            </div>

            {linkedTorrents.length > 4 && !torrentSearch && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-zinc-400 hover:text-zinc-200 h-8"
                onClick={() => {
                  setIsTorrentsExpanded(!isTorrentsExpanded)
                }}
              >
                {isTorrentsExpanded ? 'Show Less' : 'Show More'}
              </Button>
            )}
          </div>
        )}
      </div>
    </Modal>
  )
}

interface ProductionCountry {
  iso_3166_1: string
  name: string
}

// Start of DiscoveryPage

const CountryFlags = ({ countries }: { countries?: ProductionCountry[] }) => {
  if (!countries || countries.length === 0) return null

  return (
    <div className="flex -space-x-1">
      {countries.slice(0, 3).map((c, idx) => (
        <div
          key={c.iso_3166_1 || c.name || `country-${String(idx)}`}
          className="relative z-0 hover:z-10 transition-all transform hover:scale-110"
          title={c.name}
        >
          <span className="text-base drop-shadow-md filter cursor-help">
            {c.iso_3166_1
              ? c.iso_3166_1.toUpperCase().replaceAll(/./g, (char) => {
                  const codePoint = char.codePointAt(0)
                  return codePoint
                    ? String.fromCodePoint(127397 + codePoint)
                    : ''
                })
              : ''}
          </span>
        </div>
      ))}
    </div>
  )
}

const DiscoveryPage = () => {
  const { t } = useTranslation()
  const [searchQuery, setSearchQuery] = useState('')
  const debouncedQuery = useDebounce(searchQuery, 500)

  const [contentType, setContentType] = useState<'movie' | 'tv'>('movie')
  const [feedType, setFeedType] = useState<
    'trending' | 'personal' | 'rated' | 'library'
  >('library')

  const [selectedMedia, setSelectedMedia] = useState<TmdbMedia | null>(null)
  const [isSyncing, setIsSyncing] = useState(false)

  const { data: displayData, isLoading } = useQuery({
    queryKey: ['discovery', feedType, contentType, debouncedQuery],
    queryFn: () => {
      if (debouncedQuery) return searchDiscovery(debouncedQuery)
      if (feedType === 'personal') return getPersonalRecommendations() // Note: check backend impl
      if (feedType === 'rated') return getRatedMedia(contentType)
      if (feedType === 'library') return getLibrary(contentType)
      return getTrending(contentType)
    },
  })

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      const { matched } = await syncLibrary()
      toast.success(`Library synced. Matched ${String(matched)} films.`)
      // Invalidate queries to refresh "in_library" badges
      // queryClient.invalidateQueries({ queryKey: ["discovery"] }); // need queryClient
    } catch {
      toast.error('Failed to sync library')
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <div>
      <div className="flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4 mb-8">
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4 w-full">
          {/* Feed Type Toggles */}
          <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg p-1 self-start md:self-auto">
            <button
              onClick={() => {
                setFeedType('library')
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                feedType === 'library'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Library
            </button>

            <button
              onClick={() => {
                setFeedType('trending')
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                feedType === 'trending'
                  ? 'bg-zinc-800 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Trending
            </button>

            <button
              onClick={() => {
                setFeedType('rated')
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                feedType === 'rated'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Rated
            </button>

            <button
              onClick={() => {
                setFeedType('personal')
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                feedType === 'personal'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              For You
            </button>
          </div>
          {/* Content Type Toggles */}
          <div
            className={`flex bg-zinc-900 border border-zinc-800 rounded-lg p-1 transition-opacity self-start md:self-auto ${
              feedType === 'personal'
                ? 'invisible opacity-0'
                : 'visible opacity-100'
            }`}
            aria-hidden={feedType === 'personal'}
          >
            <button
              onClick={() => {
                setContentType('movie')
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                contentType === 'movie'
                  ? 'bg-zinc-800 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
              tabIndex={feedType === 'personal' ? -1 : 0}
            >
              {t('discovery.movies')}
            </button>
            <button
              onClick={() => {
                setContentType('tv')
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                contentType === 'tv'
                  ? 'bg-zinc-800 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
              tabIndex={feedType === 'personal' ? -1 : 0}
            >
              {t('discovery.tv_shows')}
            </button>
          </div>
          <div className="flex-1" /> {/* Spacer */}
          <div className="flex items-center gap-2 w-full md:w-auto">
            <div className="relative w-full md:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-zinc-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                }}
                placeholder={t('discovery.search_placeholder')}
                className="w-full bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              />
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => {
                void handleSync()
              }}
              disabled={isSyncing}
              title="Sync Library"
            >
              {isSyncing ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RefreshCw className="size-4" />
              )}
            </Button>{' '}
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-8 animate-spin text-zinc-500" />
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {displayData?.map((media) => (
            <button
              key={media.id}
              type="button"
              className="group relative aspect-[2/3] bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800 hover:border-violet-500/50 transition-all cursor-pointer text-left p-0"
              onClick={() => {
                setSelectedMedia(media)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  setSelectedMedia(media)
                }
              }}
            >
              {media.poster_path ? (
                <img
                  src={`https://image.tmdb.org/t/p/w500${media.poster_path}`}
                  alt={media.title || media.name}
                  className="size-full  object-cover transition-transform duration-500 group-hover:scale-110"
                />
              ) : (
                <div className="size-full  flex items-center justify-center text-zinc-700">
                  ?
                </div>
              )}

              <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/90 via-black/60 to-transparent pt-12 opacity-0 group-hover:opacity-100 transition-opacity">
                <h4 className="text-sm font-medium text-white line-clamp-2 leading-tight">
                  {media.title || media.name}
                </h4>
                {(media.original_title || media.original_name) &&
                  (media.original_title !== media.title ||
                    media.original_name !== media.name) && (
                    <div className="text-[10px] text-zinc-400 truncate mt-0.5">
                      {media.original_title || media.original_name}
                    </div>
                  )}
                {(media.vote_average > 0 || media.kp_rating) && (
                  <div className="flex items-center gap-2 mt-2">
                    <Star className="size-3 fill-amber-400 text-amber-400" />
                    <span className="text-xs text-zinc-300">
                      {media.vote_average.toFixed(1)}
                    </span>
                    {media.kp_rating && (
                      <>
                        <span className="text-xs text-zinc-500">•</span>
                        <span className="px-1 py-0.5 bg-orange-600/90 text-[9px] font-bold text-white rounded-[3px]">
                          KP {media.kp_rating}
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="absolute top-2 left-2 z-10">
                {(media.release_date || media.first_air_date) && (
                  <div className="bg-black/60 backdrop-blur-md px-1.5 py-0.5 rounded text-[10px] font-medium text-white/90 border border-white/10 shadow-sm">
                    {
                      (media.release_date || media.first_air_date)?.split(
                        '-',
                      )[0]
                    }
                  </div>
                )}
              </div>

              <div className="absolute top-2 right-2 z-10 flex flex-col gap-1.5 items-end">
                {(media.torrents_count || 0) > 0 && (
                  <div
                    className="bg-green-500 text-white p-1 rounded-full shadow-md"
                    title={`${String(media.torrents_count)} torrents available`}
                  >
                    <Download className="size-3" />
                  </div>
                )}
                {(() => {
                  let countries: ProductionCountry[] = []
                  if (
                    media.production_countries &&
                    media.production_countries.length > 0
                  ) {
                    countries = media.production_countries
                  } else if (
                    media.origin_country &&
                    media.origin_country.length > 0
                  ) {
                    countries = media.origin_country.map((c) => ({
                      iso_3166_1: c,
                      name: c,
                    }))
                  }

                  if (countries.length === 0) return null

                  let flagsCountries = countries
                  if (media.media_type === 'movie') {
                    flagsCountries = media.production_countries || countries
                  } else if (media.origin_country) {
                    flagsCountries = media.origin_country.map((c) => ({
                      iso_3166_1: c,
                      name: c,
                    }))
                  }

                  return <CountryFlags countries={flagsCountries} />
                })()}
              </div>
            </button>
          ))}
        </div>
      )}

      {selectedMedia && (
        <MediaModal
          media={selectedMedia}
          onClose={() => {
            setSelectedMedia(null)
          }}
        />
      )}
    </div>
  )
}
export default DiscoveryPage
