import { Tooltip } from 'components/ui/Tooltip'
import { Select } from 'components/ui/Select'
import type { User } from 'types'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUsers, updateUserStatus } from 'api'
import {
  Users,
  AlertCircle,
  ShieldCheck,
  UserCheck,
  UserX,
  Scan,
  Lock,
} from 'lucide-react'
import { Card } from 'components/ui/Card'
import { Button } from 'components/ui/Button'
import { Link } from '@tanstack/react-router'
import { clsx } from 'clsx'
import { useState } from 'react'
import { Modal } from 'components/ui/Modal'
import { Input } from 'components/ui/Input'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

const SettingsUsers = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })
  const [passwordModalUser, setPasswordModalUser] = useState<User | null>(null)
  const [newPassword, setNewPassword] = useState('')

  const updateStatusMut = useMutation({
    mutationFn: updateUserStatus,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] })
      setPasswordModalUser(null)
      setNewPassword('')
    },
    onError: (err: unknown) => {
      toast.error(
        t('common.error') +
          ': ' +
          (err instanceof Error ? err.message : String(err)),
      )
    },
  })

  const roleOptions = [
    {
      value: 'guest',
      label: t('users.roles.guest'),
      icon: <UserX className="size-4  text-zinc-500" />,
    },
    {
      value: 'authorized',
      label: t('users.roles.authorized'),
      icon: <UserCheck className="size-4  text-green-400" />,
    },
    {
      value: 'admin',
      label: t('users.roles.admin'),
      icon: <ShieldCheck className="size-4  text-violet-400" />,
    },
  ]

  const getUserRole = (user: User) => {
    if (user.is_admin) return 'admin'
    if (user.is_authorized) return 'authorized'
    return 'guest'
  }

  const handleRoleChange = (userId: number | string, role: string) => {
    const updates = {
      is_admin: role === 'admin',
      is_authorized: role === 'authorized' || role === 'admin',
    }

    toast.promise(updateStatusMut.mutateAsync({ id: userId, ...updates }), {
      loading: t('users.role_update.loading'),
      success: t('users.role_update.success'),
      error: t('users.role_update.error'),
    })
  }

  const handlePasswordSave = () => {
    if (!passwordModalUser) return

    toast.promise(
      updateStatusMut.mutateAsync({
        id: passwordModalUser.id,
        password: newPassword,
      }),
      {
        loading: t('users.password.saving'),
        success: t('users.password.saved', {
          name: passwordModalUser.name || 'User',
        }),
        error: t('users.password.failed'),
      },
    )
  }

  const toggleTfa = (user: User) => {
    const newStatus = !user.is_tfa_enabled
    toast.promise(
      updateStatusMut.mutateAsync({ id: user.id, is_tfa_enabled: newStatus }),
      {
        loading: t('users.tfa.updating'),
        success: `TFA ${newStatus ? t('users.tfa.enabled') : t('users.tfa.disabled')}`,
        error: t('users.tfa.failed'),
      },
    )
  }

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
          className="px-4 py-2 text-sm font-medium border-b-2 border-violet-500 text-violet-400"
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
            <Users className="size-5  text-violet-400" />
            {t('users.title')}
          </h2>
          <p className="text-zinc-500 text-sm mt-1">{t('users.subtitle')}</p>
        </div>
      </div>

      <div className="grid gap-4">
        {users?.map((user: User) => {
          let avatarBg = 'bg-zinc-800 text-zinc-400'
          let roleBadgeBg = 'bg-zinc-800 text-zinc-400'
          let roleText = t('users.status.guest')

          if (user.is_admin) {
            avatarBg = 'bg-violet-500/20 text-violet-400'
            roleBadgeBg = 'bg-violet-500/10 text-violet-400'
            roleText = t('users.status.admin')
          } else if (user.is_authorized) {
            avatarBg = 'bg-green-500/20 text-green-400'
            roleBadgeBg = 'bg-green-500/10 text-green-400'
            roleText = t('users.status.authorized')
          }

          return (
            <Card
              key={user.id}
              className="flex items-center justify-between p-4 group"
            >
              <div className="flex items-center gap-4">
                <div
                  className={clsx(
                    'size-12  rounded-full flex items-center justify-center text-lg font-bold transition-colors',
                    avatarBg,
                  )}
                >
                  {user.name?.[0] || 'U'}
                </div>
                <div>
                  <h3 className="font-medium text-zinc-200 flex items-center gap-2 text-lg">
                    {user.name || t('users.status.unknown')}
                    {user.username && (
                      <span className="text-zinc-500 text-sm font-normal">
                        @{user.username}
                      </span>
                    )}
                    {user.is_admin && (
                      <ShieldCheck className="size-4  text-violet-400" />
                    )}
                    {!user.is_admin && user.is_authorized && (
                      <UserCheck className="size-4  text-green-400" />
                    )}
                  </h3>
                  <div className="text-xs text-zinc-500 font-mono mt-0.5 flex items-center gap-2">
                    ID: {user.chat_id}
                    <span
                      className={clsx(
                        'px-1.5 rounded text-[10px] uppercase font-bold tracking-wider',
                        roleBadgeBg,
                      )}
                    >
                      {roleText}
                    </span>
                    {user.is_tfa_enabled && (
                      <span className="bg-sky-500/10 text-sky-400 px-1.5 rounded text-[10px] uppercase font-bold tracking-wider">
                        {t('users.tfa.on')}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <Tooltip
                  content={
                    user.is_tfa_enabled
                      ? t('users.tfa.disable')
                      : t('users.tfa.enable')
                  }
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    className={clsx(
                      'size-9  px-0',
                      user.is_tfa_enabled
                        ? 'text-sky-400 hover:text-sky-300 hover:bg-sky-500/10'
                        : 'text-zinc-600 hover:text-zinc-400',
                    )}
                    onClick={() => {
                      toggleTfa(user)
                    }}
                    isLoading={updateStatusMut.isPending}
                  >
                    <Scan className="size-5 " />
                  </Button>
                </Tooltip>

                <Tooltip content={t('users.password.set_tooltip')}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={clsx(
                      'size-9  px-0',
                      user.password
                        ? 'text-amber-400 hover:text-amber-300 hover:bg-amber-500/10'
                        : 'text-zinc-600 hover:text-zinc-400',
                    )}
                    onClick={() => {
                      setPasswordModalUser(user)
                    }}
                  >
                    <Lock className="size-5 " />
                  </Button>
                </Tooltip>

                <div className="w-px h-6 bg-zinc-800 self-center mx-1" />

                <div className="w-40">
                  <Select
                    value={getUserRole(user)}
                    onChange={(val) => {
                      handleRoleChange(user.id, String(val))
                    }}
                    options={roleOptions}
                  />
                </div>
              </div>
            </Card>
          )
        })}

        {users?.length === 0 && (
          <div className="text-center py-12 text-zinc-500 bg-zinc-900/30 rounded-xl border border-dashed border-zinc-800">
            <Users className="size-12  mx-auto mb-3 opacity-20" />
            {t('users.no_users')}
          </div>
        )}
      </div>

      <div className="mt-8 p-4 bg-blue-500/5 border border-blue-500/10 rounded-lg flex gap-3 text-sm text-blue-400/80">
        <AlertCircle className="size-5  flex-shrink-0" />
        <p>{t('users.info_hint')}</p>
      </div>

      <Modal
        isOpen={!!passwordModalUser}
        onClose={() => {
          setPasswordModalUser(null)
          setNewPassword('')
        }}
        title={t('users.password.set_title', {
          name: passwordModalUser?.name || 'User',
        })}
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-zinc-400 mb-1 block">
              {t('users.password.new')}
            </label>
            <Input
              type="password"
              placeholder={t('users.password.placeholder')}
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value)
              }}
              className="bg-zinc-950"
            />
            <p className="text-xs text-zinc-500 mt-2">
              {t('users.password.hint')}
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              onClick={() => {
                setPasswordModalUser(null)
              }}
            >
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handlePasswordSave}
              isLoading={updateStatusMut.isPending}
              className="bg-violet-600 text-white hover:bg-violet-700"
            >
              {t('users.password.save')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
export default SettingsUsers
