import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Category } from 'types'
import { getCategories, createCategory, updateCategory, deleteCategory } from 'api'
import { AxiosError } from 'axios'
import { Plus, Trash2, Edit2, Folder } from 'lucide-react'
import { useState } from 'react'
import { Modal } from 'components/ui/Modal'
import { Button } from 'components/ui/Button'
import { Input } from 'components/ui/Input'
import { Card } from 'components/ui/Card'
import { Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

const CategoryModal = ({ category, onClose }: { category?: Category | null, onClose: () => void }) => {
    const { t } = useTranslation()
    const queryClient = useQueryClient()
    const [name, setName] = useState(category?.name || '')
    const [icon, setIcon] = useState(category?.icon || '')
    const [folder, setFolder] = useState(category?.folder || '')
    const [isLoading, setIsLoading] = useState(false)

    const isEdit = !!category

    const createMut = useMutation({
        mutationFn: createCategory,
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ['categories'] })
            onClose()
        },
        onError: (e: AxiosError<{ detail: string }>) => { alert(e.response?.data.detail || t('categories.form.error_create')); }
    })

    const updateMut = useMutation({
        mutationFn: updateCategory,
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ['categories'] })
            onClose()
        },
        onError: (e: AxiosError<{ detail: string }>) => { alert(e.response?.data.detail || t('categories.form.error_update')); }
    })

    const handleSubmit = async () => {
        if (!name) { alert(t('categories.form.name_required')); return; }
        setIsLoading(true)
        try {
            if (category) {
                await updateMut.mutateAsync({ id: category.id, name, icon, folder })
            } else {
                const fd = new FormData()
                fd.append('name', name)
                if (icon) fd.append('icon', icon)
                if (folder) fd.append('folder', folder)
                await createMut.mutateAsync(fd)
            }
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Modal
            isOpen={true}
            onClose={onClose}
            title={isEdit ? t('categories.edit') : t('categories.create')}
        >
            <div className="space-y-4">
                <div>
                    <label className="block text-xs font-medium text-zinc-500 mb-1">{t('categories.form.name')}</label>
                    <Input value={name} onChange={(e) => { setName(e.target.value); }} className="text-zinc-200" placeholder={t('categories.form.name_placeholder')} />
                </div>
                <div>
                    <label className="block text-xs font-medium text-zinc-500 mb-1">{t('categories.form.icon')}</label>
                    <Input value={icon} onChange={(e) => { setIcon(e.target.value); }} className="text-zinc-200" placeholder={t('categories.form.icon_placeholder')} />
                </div>
                <div>
                    <label className="block text-xs font-medium text-zinc-500 mb-1">{t('categories.form.folder')}</label>
                    <Input value={folder} onChange={(e) => { setFolder(e.target.value); }} className="text-zinc-200" placeholder={t('categories.form.folder_placeholder')} />
                </div>
                <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-zinc-800">
                    <Button variant="ghost" onClick={onClose}>{t('common.cancel')}</Button>
                    <Button onClick={() => { void handleSubmit(); }} isLoading={isLoading}>{t('common.save')}</Button>
                </div>
            </div>
        </Modal>
    )
}

const SettingsCategory = () => {
    const { t } = useTranslation()
    const { data: categories, isLoading } = useQuery({ queryKey: ['categories'], queryFn: getCategories })
    const [editingCategory, setEditingCategory] = useState<Category | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const queryClient = useQueryClient()

    const deleteMut = useMutation({
        mutationFn: deleteCategory,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['categories'] }),
        onError: (e: AxiosError<{ detail: string }>) => { alert(e.response?.data.detail || t('categories.form.error_delete')); }
    })

    if (isLoading) return <div className="text-zinc-500">{t('common.loading')}</div>

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="flex gap-2 mb-8 border-b border-zinc-800">
                <Link
                    to="/settings/category"
                    className="px-4 py-2 text-sm font-medium border-b-2 border-violet-500 text-violet-400"
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
            </div>

            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                        <Folder className="size-5  text-violet-400" />
                        {t('categories.title')}
                    </h2>
                    <p className="text-zinc-500 text-sm mt-1">{t('categories.subtitle')}</p>
                </div>
                <Button onClick={() => { setIsCreating(true); }}>
                    <Plus className="size-4  mr-2" />
                    {t('categories.add')}
                </Button>
            </div>

            <div className="grid gap-4">
                {categories?.map((cat: Category) => (
                    <Card key={cat.id} className="flex items-center justify-between p-4 group">
                        <div className="flex items-center gap-4">
                            <div className="size-10  rounded-full bg-zinc-800 flex items-center justify-center text-xl">
                                {cat.icon || <Folder className="size-5  text-zinc-500" />}
                            </div>
                            <div>
                                <h3 className="font-medium text-zinc-200">{cat.name}</h3>
                                {cat.folder && (
                                    <div className="text-xs text-zinc-500 font-mono mt-0.5">
                                        {cat.folder}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="sm" onClick={() => { setEditingCategory(cat); }}>
                                <Edit2 className="size-4 " />
                            </Button>
                            <Button
                                variant="danger"
                                size="sm"
                                className="bg-red-500/10 text-red-400 hover:bg-red-500/20"
                                onClick={() => { if (confirm(t('categories.form.delete_confirm'))) deleteMut.mutate(cat.id) }}
                            >
                                <Trash2 className="size-4 " />
                            </Button>
                        </div>
                    </Card>
                ))}

                {categories?.length === 0 && (
                    <div className="text-center py-12 text-zinc-500 bg-zinc-900/30 rounded-xl border border-dashed border-zinc-800">
                        <Folder className="size-12  mx-auto mb-3 opacity-20" />
                        {t('categories.no_categories')}
                    </div>
                )}
            </div>

            {(isCreating || editingCategory) && (
                <CategoryModal
                    category={editingCategory}
                    onClose={() => {
                        setIsCreating(false)
                        setEditingCategory(null)
                    }}
                />
            )}
        </div>
    )
}
export default SettingsCategory
