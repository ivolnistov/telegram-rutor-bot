import { useTranslation } from 'react-i18next'
import { Select } from './ui/Select'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMe, updateUserStatus } from 'api'
import { useEffect } from 'react'
import { toast } from 'sonner'

const LanguageSwitcher = () => {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    retry: false,
  })

  const { mutate: updateLanguage } = useMutation({
    mutationFn: ({ id, language }: { id: number; language: string }) =>
      updateUserStatus({ id, language }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['me'] })
      toast.success(t('common.saved'))
    },
    onError: () => {
      toast.error(t('common.error'))
    },
  })

  useEffect(() => {
    if (user?.language && user.language !== i18n.language) {
      void i18n.changeLanguage(user.language)
    }
  }, [user?.language, i18n])

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'ru', label: 'Русский' },
  ]

  const currentLanguage =
    languages.find((l) => l.value === i18n.language) || languages[0]

  const handleLanguageChange = (value: string | number) => {
    const newLang = String(value)
    void i18n.changeLanguage(newLang)
    if (user) {
      updateLanguage({ id: user.id, language: newLang })
    }
  }

  return (
    <div className="w-32">
      <Select
        value={currentLanguage.value}
        onChange={handleLanguageChange}
        options={languages}
      />
    </div>
  )
}

export default LanguageSwitcher
