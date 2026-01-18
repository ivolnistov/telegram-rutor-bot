import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSearches, createSearch, deleteSearch, executeSearch, updateSearch, getSearchSubscribers, addSearchSubscriber, removeSearchSubscriber, getCategories, getUsers } from 'api'
import { AxiosError } from 'axios'
import { Play, Plus, Clock, ExternalLink, Trash2, Users, Info } from 'lucide-react'
import { useState } from 'react'
import { CronScheduler } from 'components/shared/CronScheduler'
import { Modal } from 'components/ui/Modal'
import { Button } from 'components/ui/Button'
import { Input } from 'components/ui/Input'
import { Card } from 'components/ui/Card'
import { Select } from 'components/ui/Select'
import { Tooltip } from 'components/ui/Tooltip'
import type { Category, Search, User } from 'types'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

// Helper for relative time (or date)
const formatDate = (dateStr?: string | null, locale: string = 'en') => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    })
}

const EditSearchModal = ({ search, onClose }: { search: Search, onClose: () => void }) => {
    const { t, i18n } = useTranslation()
    const queryClient = useQueryClient()
    const [url, setUrl] = useState(search.url)
    const [cron, setCron] = useState(search.cron)
    const [category, setCategory] = useState(search.category || '')
    const [newSubscriberId, setNewSubscriberId] = useState('')

    const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: getCategories })
    const { data: users } = useQuery({ queryKey: ['users'], queryFn: getUsers })

    const [localSubscribers, setLocalSubscribers] = useState<User[]>([])
    const [addedSubIds, setAddedSubIds] = useState<Set<number>>(new Set())
    const [removedSubIds, setRemovedSubIds] = useState<Set<number>>(new Set())

    // Fetch subscribers
    const { data: subscribers, isSuccess } = useQuery({
        queryKey: ['subscribers', search.id],
        queryFn: () => getSearchSubscribers(search.id)
    })

    // Sync subscribers on load
    const [isSubsLoaded, setIsSubsLoaded] = useState(false)
    if (isSuccess && !isSubsLoaded) {
        setLocalSubscribers(subscribers)
        setIsSubsLoaded(true)
    }

    const updateMut = useMutation({
        mutationFn: updateSearch,
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ['searches'] })
            onClose()
            toast.success(t('searches.messages.updated'))
        }
    })

    const deleteMut = useMutation({
        mutationFn: deleteSearch,
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ['searches'] })
            onClose()
            toast.success(t('searches.messages.deleted'))
        }
    })

    const addSubMut = useMutation({
        mutationFn: ({ id, chatId }: { id: number | string, chatId: number | string }) => addSearchSubscriber(id, chatId),
    })

    const removeSubMut = useMutation({
        mutationFn: ({ id, userId }: { id: number | string, userId: number | string }) => removeSearchSubscriber(id, userId),
    })

    const catOptions = categories?.map((c: Category) => ({
        value: c.name,
        label: c.name,
        icon: c.icon
    })) || []

    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

    const handleAddSubscriber = (chatIdStr: string) => {
        const chatId = Number(chatIdStr)
        const userToAdd = users?.find(u => u.chat_id === chatId)
        if (!userToAdd) return

        // Check if already in list
        if (localSubscribers.some(s => s.id === userToAdd.id)) return

        // Add to local list
        setLocalSubscribers([...localSubscribers, userToAdd])

        // Track addition
        const newAdded = new Set(addedSubIds)
        newAdded.add(chatId)
        setAddedSubIds(newAdded)

        // If it was in removed list, remove it from there (re-adding a removed user)
        if (removedSubIds.has(userToAdd.id)) {
            const newRemoved = new Set(removedSubIds)
            newRemoved.delete(userToAdd.id)
            setRemovedSubIds(newRemoved)
        }

        setNewSubscriberId('')
    }

    const handleRemoveSubscriber = (userId: number) => {
        setLocalSubscribers(localSubscribers.filter(s => s.id !== userId))

        const newRemoved = new Set(removedSubIds)
        newRemoved.add(userId)
        setRemovedSubIds(newRemoved)

        // If it was in added list, remove it from there
        // Note: addedSubIds stores chat_id, removedSubIds stores user.id
    }

    const handleSave = async () => {
        try {
            // Update search details
            await updateMut.mutateAsync({ id: search.id, url, cron, category })

            // Process removals
            for (const userId of removedSubIds) {
                const wasOriginallySubscribed = subscribers?.some(s => s.id === userId)
                if (wasOriginallySubscribed) {
                    await removeSubMut.mutateAsync({ id: search.id, userId })
                }
            }

            // Process additions
            for (const chatId of addedSubIds) {
                const currentUser = users?.find(u => u.chat_id === chatId)
                if (currentUser && localSubscribers.some(s => s.id === currentUser.id)) {
                    // Still in list, so add
                    await addSubMut.mutateAsync({ id: search.id, chatId })
                }
            }

            await queryClient.invalidateQueries({ queryKey: ['searches'] })
            await queryClient.invalidateQueries({ queryKey: ['subscribers', search.id] })
            onClose()
            toast.success(t('searches.messages.updated'))
        } catch (e) {
            console.error(e)
            toast.error(t('common.error'))
        }
    }

    const userOptions = users
        ?.filter(u => !localSubscribers.some(s => s.id === u.id)) // Filter out already added
        .map((u: User) => ({
            value: u.chat_id,
            label: u.name || String(u.chat_id)
        })) || []

    return (
        <Modal
            isOpen={true}
            onClose={onClose}
            title={t('searches.edit_title', { id: search.id })}
        >
            <div className="space-y-6">
                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-zinc-500 mb-1">{t('searches.url')}</label>
                        <Input
                            value={url}
                            onChange={(e) => { setUrl(e.target.value); }}
                            className="text-zinc-200"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-zinc-500 mb-1">{t('searches.category_label')}</label>
                        <Select
                            value={category}
                            onChange={(val) => { setCategory(String(val)); }}
                            options={catOptions}
                            placeholder={t('searches.select_category')}
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-zinc-500 mb-1">{t('searches.cron_label')}</label>
                        <CronScheduler value={cron} onChange={setCron} />
                    </div>
                </div>

                {/* Subscribers Section */}
                <div className="pt-4 border-t border-zinc-800">
                    <h4 className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                        <Users className="size-4  text-zinc-500" />
                        {t('searches.subscribers_label')}
                    </h4>

                    <div className="space-y-2 mb-3">
                        {localSubscribers.map((sub: User) => (
                            <div key={sub.id} className="flex items-center justify-between bg-zinc-900/50 p-2 rounded-lg border border-zinc-800">
                                <div className="flex items-center gap-2">
                                    <div className="size-6  rounded-full bg-violet-500/10 flex items-center justify-center text-xs text-violet-400 font-medium">
                                        {sub.name?.[0] || 'U'}
                                    </div>
                                    <div className="text-xs">
                                        <span className="text-zinc-300 block">{sub.name || `User ${String(sub.chat_id)} `}</span>
                                        <span className="text-zinc-600 font-mono">{sub.chat_id}</span>
                                    </div>
                                </div>
                                <button
                                    onClick={() => { handleRemoveSubscriber(sub.id); }}
                                    className="p-1.5 hover:bg-red-500/10 text-zinc-600 hover:text-red-500 rounded transition-colors"
                                    title={t('common.delete')}
                                >
                                    <Trash2 className="size-3.5 " />
                                </button>
                            </div>
                        ))}
                        {localSubscribers.length === 0 && (
                            <div className="text-xs text-zinc-600 italic px-2">{t('searches.no_subscribers')}</div>
                        )}
                    </div>

                    <div className="flex gap-2 items-end">
                        <div className="flex-1">
                            <Select
                                value={newSubscriberId}
                                onChange={(val) => { handleAddSubscriber(String(val)); }}
                                options={userOptions}
                                placeholder={t('searches.select_user')}
                            />
                        </div>
                    </div>
                </div>

                <div className="flex gap-3 justify-between mt-8 pt-4 border-t border-zinc-800">
                    <Button
                        variant="danger"
                        onClick={() => { setShowDeleteConfirm(true); }}
                    >
                        {t('searches.delete_confirm_title')}
                    </Button>
                    <div className="flex gap-3">
                        <Button variant="ghost" onClick={onClose}>{t('common.cancel')}</Button>
                        <Button
                            onClick={() => void handleSave()}
                            isLoading={updateMut.isPending || addSubMut.isPending || removeSubMut.isPending}
                        >
                            {t('common.save')}
                        </Button>
                    </div>
                </div>
            </div>

            {/* Delete Confirmation Modal */}
            <Modal
                isOpen={showDeleteConfirm}
                onClose={() => { setShowDeleteConfirm(false); }}
                title={t('searches.delete_confirm_title')}
                className="max-w-sm"
            >
                <div>
                    <p className="text-zinc-300 mb-6">
                        {t('searches.delete_confirm_desc')}
                    </p>
                    <div className="flex justify-end gap-3">
                        <Button
                            variant="ghost"
                            onClick={() => { setShowDeleteConfirm(false); }}
                        >
                            {t('common.cancel')}
                        </Button>
                        <Button
                            variant="danger"
                            onClick={() => {
                                deleteMut.mutate(search.id);
                                setShowDeleteConfirm(false);
                            }}
                        >
                            {t('common.delete')}
                        </Button>
                    </div>
                </div>
            </Modal>
        </Modal>
    )
}

const CreateSearchModal = ({ onClose }: { onClose: () => void }) => {
    const { t } = useTranslation()
    const queryClient = useQueryClient()
    const [url, setUrl] = useState('')
    const [cron, setCron] = useState('0 12 * * *')
    const [category, setCategory] = useState('')
    const [subscribers, setSubscribers] = useState<string[]>([''])
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [errors, setErrors] = useState<Record<string, string>>({})

    const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: getCategories })
    const { data: users } = useQuery({ queryKey: ['users'], queryFn: getUsers })

    const createMut = useMutation({
        mutationFn: createSearch,
    })

    const addSubMut = useMutation({
        mutationFn: ({ id, chatId }: { id: number | string, chatId: number | string }) => addSearchSubscriber(id, chatId),
    })

    const handleCreate = async () => {
        setErrors({})
        const newErrors: Record<string, string> = {}
        const validSubs = subscribers.filter(s => s.trim())

        if (!url) newErrors.url = t('searches.validation.url_required')
        else if (!url.includes('rutor')) newErrors.url = t('searches.validation.url_invalid')

        if (!category) newErrors.category = t('searches.validation.category_required')

        if (validSubs.length === 0) newErrors.subscribers = t('searches.validation.subscribers_required')

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors)
            return
        }

        setIsSubmitting(true)
        try {
            // 1. Create search with first subscriber
            const firstSub = validSubs[0]
            const formData = new FormData()
            formData.append('url', url)
            formData.append('cron', cron)
            if (category) formData.append('category', category)
            // Backend handles linking existing user by chat_id or creating new one
            formData.append('new_chat_id', firstSub)

            const res = await createMut.mutateAsync(formData)
            const searchId = res.id

            // 2. Add remaining subscribers
            const otherSubs = validSubs.slice(1)
            await Promise.all(otherSubs.map(chatId =>
                addSubMut.mutateAsync({ id: searchId, chatId })
            ))

            await queryClient.invalidateQueries({ queryKey: ['searches'] })
            toast.success(t('searches.messages.created'))
            onClose()
        } catch (e: unknown) {
            const err = e as AxiosError<{ detail: string }>
            toast.error(err.response?.data.detail || t('searches.messages.failed_create'))
        } finally {
            setIsSubmitting(false)
        }
    }

    const catOptions = categories?.map((c: Category) => ({
        value: c.name,
        label: c.name,
        icon: c.icon
    })) || []

    const userOptions = users?.map((u: User) => ({
        value: u.chat_id,
        label: u.name || String(u.chat_id)
    })) || []

    return (
        <Modal
            isOpen={true}
            onClose={onClose}
            title={t('searches.create_title')}
        >
            <div className="space-y-6">
                <div>
                    <label className="block text-xs font-medium text-zinc-500 mb-1">{t('searches.url')}</label>
                    <Input
                        value={url}
                        onChange={(e) => {
                            setUrl(e.target.value)
                            if (errors.url) setErrors({ ...errors, url: '' })
                        }}
                        placeholder={t('searches.url_placeholder')}
                        className={`text-zinc-200 ${errors.url ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}`}
                    />
                    {errors.url && <p className="text-red-500 text-xs mt-1">{errors.url}</p>}
                </div>

                <div>
                    <label className="block text-xs font-medium text-zinc-500 mb-1">{t('searches.category_label')}</label>
                    <Select
                        value={category}
                        onChange={(val) => {
                            setCategory(String(val))
                            if (errors.category) setErrors({ ...errors, category: '' })
                        }}
                        options={catOptions}
                        placeholder={t('searches.select_category')}
                        className={errors.category ? 'border-red-500' : ''}
                    />
                    {errors.category && <p className="text-red-500 text-xs mt-1">{errors.category}</p>}
                </div>

                <div>
                    <label className="block text-xs font-medium text-zinc-500 mb-1 flex items-center gap-1">
                        {t('searches.cron_label')}
                        <Tooltip content={`Cron Expression: ${cron}`}>
                            <div className="cursor-help text-zinc-600 hover:text-zinc-400">
                                <Info className="size-3" />
                            </div>
                        </Tooltip>
                    </label>
                    <CronScheduler value={cron} onChange={setCron} />
                </div>

                <div className="pt-4 border-t border-zinc-800">
                    <h4 className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                        <Users className="size-4  text-zinc-500" />
                        {t('searches.subscribers_label')}
                    </h4>
                    {errors.subscribers && <p className="text-red-500 text-xs mb-2">{errors.subscribers}</p>}
                    <div className="space-y-2">
                        {subscribers.map((sub, idx) => (
                            <div key={idx} className="flex gap-2 items-center">
                                <div className="flex-1">
                                    <Select
                                        value={sub}
                                        onChange={(val) => {
                                            const newSubs = [...subscribers]
                                            newSubs[idx] = String(val)
                                            setSubscribers(newSubs)
                                            if (errors.subscribers) setErrors({ ...errors, subscribers: '' })
                                        }}
                                        options={userOptions}
                                        placeholder={t('searches.select_user')}
                                    />
                                </div>
                                {subscribers.length > 1 && (
                                    <Button
                                        variant="ghost"
                                        className="size-[38px]  px-0 text-zinc-500 hover:text-red-400"
                                        onClick={() => { setSubscribers(subscribers.filter((_, i) => i !== idx)); }}
                                    >
                                        <Trash2 className="size-4 " />
                                    </Button>
                                )}
                            </div>
                        ))}
                        <Button
                            variant="secondary"
                            size="sm"
                            className="w-full mt-2"
                            onClick={() => { setSubscribers([...subscribers, '']); }}
                        >
                            <Plus className="size-4  mr-2" />
                            {t('searches.add_subscriber')}
                        </Button>
                    </div>
                </div>

                <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-zinc-800">
                    <Button variant="ghost" onClick={onClose}>{t('common.cancel')}</Button>
                    <Button
                        onClick={() => { void handleCreate(); }}
                        isLoading={isSubmitting}
                    >
                        {t('searches.create_title')}
                    </Button>
                </div>
            </div>
        </Modal>
    )
}

const AddSearchSection = () => {
    const { t } = useTranslation()
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className="mb-8 flex justify-end">
            <Button onClick={() => { setIsOpen(true); }} className="flex items-center gap-2">
                <Plus className="size-5 " />
                {t('searches.add')}
            </Button>
            {isOpen && <CreateSearchModal onClose={() => { setIsOpen(false); }} />}
        </div>
    )
}

const SearchesList = () => {
    const { t, i18n } = useTranslation()
    const { data: searches, isLoading } = useQuery({ queryKey: ['searches'], queryFn: getSearches })
    const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: getCategories })
    const [selectedCategory, setSelectedCategory] = useState<string>('')
    const [editingSearch, setEditingSearch] = useState<Search | null>(null)
    const executeMut = useMutation({
        mutationFn: ({ id, chatId }: { id: number | string, chatId: number | string }) => executeSearch(id, chatId),
        onSuccess: () => { toast.success(t('searches.messages.task_started')) },
        onError: (err: AxiosError<{ detail: string }>) => {
            toast.error(err.response?.data.detail || t('searches.messages.failed_task'))
        }
    })

    if (isLoading) return <div className="text-zinc-500">{t('common.loading')}</div>

    const filteredSearches = searches?.filter((s: Search) =>
        !selectedCategory || s.category === selectedCategory
    )

    const catOptions = [
        { value: '', label: t('searches.all_categories') },
        ...(categories?.map((c: Category) => ({
            value: c.name,
            label: c.name,
            icon: c.icon
        })) || [])
    ]

    return (
        <div className="mb-16">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                <h3 className="text-xl font-semibold flex items-center gap-3">
                    <Clock className="size-5  text-zinc-400" />
                    {t('searches.title')}
                </h3>
                <div className="w-full sm:w-64">
                    <Select
                        value={selectedCategory}
                        onChange={(val) => { setSelectedCategory(String(val)); }}
                        options={catOptions}
                        placeholder={t('searches.filter_category')}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredSearches?.map((search: Search) => (
                    <Card
                        key={search.id}
                        onClick={() => { setEditingSearch(search); }}
                        className="cursor-pointer group flex flex-col"
                    >
                        <div className="flex justify-between items-start mb-2">
                            <div className="flex flex-col">
                                <span className="bg-zinc-800 text-zinc-400 text-xs px-2 py-1 rounded font-mono w-fit mb-1">#{search.id}</span>
                                {search.category && (
                                    <span className="text-[10px] text-violet-400 uppercase tracking-wider font-bold">{search.category}</span>
                                )}
                            </div>
                            <div className="flex items-center gap-2 text-xs text-zinc-500">
                                <Clock className="size-3 " />
                                {formatDate(search.last_success, i18n.language)}
                            </div>
                        </div>

                        <div className="text-zinc-200 font-medium group-hover:text-violet-400 transition-colors line-clamp-1 mb-2">
                            {search.url}
                        </div>

                        <div className="flex items-center justify-between mt-auto pt-4 border-t border-zinc-800/50">
                            <span className="inline-block bg-violet-500/10 text-violet-400 text-xs px-2 py-0.5 rounded border border-violet-500/20 font-mono">
                                {search.cron}
                            </span>
                            <div className="flex gap-2" onClick={e => { e.stopPropagation(); }}>
                                <a
                                    href={search.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-2 hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 rounded-lg transition-colors"
                                    title={t('common.open_link') || "Open URL"}
                                >
                                    <ExternalLink className="size-4 " />
                                </a>
                                <button
                                    onClick={() => { executeMut.mutate({ id: search.id, chatId: search.creator_id || 0 }); }}
                                    className="p-2 hover:bg-emerald-500/10 text-emerald-500/70 hover:text-emerald-500 rounded-lg transition-colors border border-transparent hover:border-emerald-500/20"
                                    title={t('common.run_now') || "Run Now"}
                                >
                                    <Play className="size-4 " />
                                </button>
                            </div>
                        </div>
                    </Card>
                ))}

                {filteredSearches?.length === 0 && (
                    <div className="col-span-full py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
                        {t('searches.no_searches')}
                    </div>
                )}
            </div>

            {editingSearch && (
                <EditSearchModal search={editingSearch} onClose={() => { setEditingSearch(null); }} />
            )}
        </div>
    )
}

const Home = () => {
    return (
        <div>
            <AddSearchSection />
            <SearchesList />
        </div>
    )
}

export default Home
