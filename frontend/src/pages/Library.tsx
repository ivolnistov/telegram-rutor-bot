import { useQuery } from '@tanstack/react-query'
import { getFilms, getCategories, downloadTorrent } from 'api'
import { Search, Star, Download } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useDebounce } from 'hooks/useDebounce'
import { Input } from 'components/ui/Input'
import { Card } from 'components/ui/Card'
import { Button } from 'components/ui/Button'
import { Modal } from 'components/ui/Modal'
import { Select } from 'components/ui/Select'
import type { Category, Film, Torrent } from 'types'
import { useTranslation } from 'react-i18next'

const FilmTorrentsModal = ({ film, onClose }: { film: Film, onClose: () => void }) => {
    const { t } = useTranslation()
    return (
        <Modal
            isOpen={true}
            onClose={onClose}
            title={t('library.downloads_modal', { title: film.ru_name || film.name })}
        >
            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                {film.torrents.map((torrent: Torrent) => (
                    <div key={torrent.id} className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 hover:border-violet-500/30 transition-colors">
                        <div className="flex justify-between items-start gap-4">
                            <div className="min-w-0">
                                <div className="text-sm font-medium text-zinc-200 break-words line-clamp-2" title={torrent.name}>
                                    {torrent.name}
                                </div>
                                <div className="text-xs text-zinc-500 mt-1 font-mono">
                                    {(torrent.sz / 1024 / 1024 / 1024).toFixed(2)} GB • {new Date(torrent.created).toLocaleDateString()}
                                </div>
                            </div>
                            <Button
                                size="sm"
                                className="flex-shrink-0"
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
                                <Download className="size-4 mr-2" />
                                {t('library.download')}
                            </Button>
                        </div>
                    </div>
                ))}
            </div>
            <div className="flex justify-end pt-4 border-t border-zinc-800">
                <Button variant="ghost" onClick={onClose}>{t('common.close')}</Button>
            </div>
        </Modal>
    )
}

const LibraryPage = () => {
    const { t } = useTranslation()
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedCategoryId, setSelectedCategoryId] = useState<string>('')
    const debouncedQuery = useDebounce(searchQuery, 300)
    const [selectedFilm, setSelectedFilm] = useState<Film | null>(null)

    const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: getCategories })

    const { data: films, isLoading } = useQuery({
        queryKey: ['films', debouncedQuery, selectedCategoryId],
        queryFn: () => getFilms(debouncedQuery, selectedCategoryId)
    })

    const catOptions = [
        { value: '', label: t('library.all_categories') },
        ...(categories?.map((c: Category) => ({
            value: String(c.id),
            label: c.name,
            icon: c.icon
        })) || [])
    ]

    return (
        <div>
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
                <h3 className="text-xl font-semibold">{t('library.title')}</h3>
                <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto">
                    <div className="w-full sm:w-48">
                        <Select
                            value={selectedCategoryId}
                            onChange={(val) => { setSelectedCategoryId(String(val)); }}
                            options={catOptions}
                            placeholder={t('library.all_categories')}
                        />
                    </div>
                    <div className="w-full sm:w-64">
                        <Input
                            icon={<Search className="size-4 " />}
                            type="text"
                            placeholder={t('library.search_placeholder')}
                            value={searchQuery}
                            onChange={(e) => { setSearchQuery(e.target.value); }}
                        />
                    </div>
                </div>
            </div>

            {isLoading ? (
                <div className="text-zinc-500">{t('library.loading')}</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {films?.map((film: Film) => (
                        <Card key={film.id} className="flex gap-4 p-4 hover:bg-zinc-900/50 transition-colors">
                            <div className="w-[60px] h-[90px] bg-black rounded overflow-hidden flex-shrink-0 border border-zinc-800 relative group">
                                {film.poster ? (
                                    <img src={film.poster} alt={film.name} className="size-full  object-cover transition-transform duration-500 group-hover:scale-110" />
                                ) : (
                                    <div className="size-full  flex items-center justify-center text-zinc-700 font-bold text-xl">?</div>
                                )}
                            </div>

                            <div className="flex-1 min-w-0 flex flex-col">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="text-xs font-mono text-zinc-600">#{film.id}</span>
                                    {film.rating && (
                                        <div className="flex items-center gap-1 text-xs text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">
                                            <Star className="size-3  fill-amber-400" />
                                            {film.rating}
                                        </div>
                                    )}
                                </div>

                                <h4 className="font-medium text-zinc-200 truncate pr-2" title={film.ru_name || film.name}>
                                    {film.ru_name || film.name || t('library.unknown_title')}
                                </h4>

                                {(film.name && film.name !== film.ru_name) && (
                                    <p className="text-xs text-zinc-500 truncate mt-0.5">{film.name}</p>
                                )}

                                <div className="flex items-center justify-between mt-auto pt-2">
                                    <div className="flex flex-col gap-1 text-xs text-zinc-500">
                                        <div className="flex gap-2">
                                            <span>{film.year || t('library.unknown_year')}</span>
                                            {film.country && (
                                                <span className="truncate max-w-[100px]" title={film.country}>• {film.country}</span>
                                            )}
                                        </div>
                                        {film.genres && (
                                            <div className="truncate max-w-[180px]" title={film.genres}>
                                                {film.genres}
                                            </div>
                                        )}
                                    </div>
                                    {film.torrents.length > 0 && (
                                        <Button
                                            size="sm"
                                            variant="secondary"
                                            className="h-7 text-xs px-2"
                                            onClick={() => { setSelectedFilm(film); }}
                                        >
                                            <Download className="size-3  mr-1.5" />
                                            {film.torrents.length} {t('library.files')}
                                        </Button>
                                    )}
                                </div>

                                {/* Quick list (first 2 only) */}
                                <div className="mt-3 pt-3 border-t border-zinc-800 space-y-1 overflow-hidden">
                                    {film.torrents.slice(0, 2).map((torrent: Torrent) => (
                                        <div key={torrent.id} className="flex justify-between text-[10px] text-zinc-500">
                                            <span className="truncate max-w-[150px]">{torrent.name.replace(film.name, '').trim() || torrent.name}</span>
                                            <span className="font-mono">{(torrent.sz / 1024 / 1024 / 1024).toFixed(1)} GB</span>
                                        </div>
                                    ))}
                                    {film.torrents.length > 2 && (
                                        <div className="text-[10px] text-zinc-600 italic">+{film.torrents.length - 2} {t('library.more')}</div>
                                    )}
                                </div>
                            </div>
                        </Card>
                    ))}

                    {films?.length === 0 && (
                        <div className="col-span-full py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
                            {t('library.no_films')}
                        </div>
                    )}
                </div>
            )}

            {selectedFilm && (
                <FilmTorrentsModal film={selectedFilm} onClose={() => { setSelectedFilm(null); }} />
            )}
        </div>
    )
}
export default LibraryPage
