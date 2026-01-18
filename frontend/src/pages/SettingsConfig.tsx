import { useState, useEffect } from 'react'
import { checkConfig, saveConfig, type ConfigSetupRequest } from 'api'
import { Button } from 'components/ui/Button'
import { Input } from 'components/ui/Input'
import { Card } from 'components/ui/Card'
import { Check, Info, Settings as SettingsIcon, Eye, EyeOff } from 'lucide-react'
import { Tooltip } from 'components/ui/Tooltip'
import { Link } from '@tanstack/react-router'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

export default function SettingsConfig() {
    const { t } = useTranslation()
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [envVars, setEnvVars] = useState<string[]>([])

    const [telegramToken, setTelegramToken] = useState('')

    // Torrent Client State
    const [host, setHost] = useState('localhost')
    const [port, setPort] = useState(8080)
    const [username, setUsername] = useState('admin')
    const [password, setPassword] = useState('')
    const [showTorrentPassword, setShowTorrentPassword] = useState(false)
    const [seedRatioLimit, setSeedRatioLimit] = useState(1.0)
    const [seedTimeLimit, setSeedTimeLimit] = useState(2880)
    const [inactiveSeedingTimeLimit, setInactiveSeedingTimeLimit] = useState(0)

    useEffect(() => {
        const load = async () => {
            try {
                const res = await checkConfig()
                setTelegramToken(String(res.current_values.telegram_token || ''))

                setHost(String(res.current_values.qbittorrent_host || 'localhost'))
                setPort(Number(res.current_values.qbittorrent_port || 8080))
                setUsername(String(res.current_values.qbittorrent_username || 'admin'))
                setPassword(String(res.current_values.qbittorrent_password || ''))

                setSeedRatioLimit(Number(res.current_values.seed_ratio_limit || 1.0))
                setSeedTimeLimit(Number(res.current_values.seed_time_limit || 2880))
                setInactiveSeedingTimeLimit(Number(res.current_values.inactive_seeding_time_limit || 0))
                setEnvVars(res.env_vars)
            } catch (err) {
                console.error(err)
                toast.error(t('common.error'))
            } finally {
                setLoading(false)
            }
        }
        void load()
    }, [t])

    const handleSave = async () => {
        setSaving(true)

        const config: ConfigSetupRequest = {
            telegram: {
                token: telegramToken,
            },
            torrent: {
                client: "qbittorrent",
                host,
                port: port,
                username,
                password
            },
            seed_ratio_limit: seedRatioLimit,
            seed_time_limit: seedTimeLimit,
            inactive_seeding_time_limit: inactiveSeedingTimeLimit
        }

        try {
            await saveConfig(config)
            toast.success(t('common.saved'))
        } catch (e: unknown) {
            if (e instanceof Error) {
                toast.error(e.message)
            } else {
                toast.error(t('common.error'))
            }
        } finally {
            setSaving(false)
        }
    }

    const isEnv = (key: string) => envVars.includes(key)

    if (loading) return <div className="text-zinc-500">{t('common.loading')}</div>

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
                    className="px-4 py-2 text-sm font-medium border-b-2 border-violet-500 text-violet-400"
                >
                    {t('settings.title')}
                </Link>
            </div>

            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                        <SettingsIcon className="size-5 text-violet-400" />
                        {t('settings.title')}
                    </h2>
                    <p className="text-zinc-500 text-sm mt-1">{t('settings.description')}</p>
                </div>
            </div>

            <Card className="p-6 space-y-8">
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-medium text-zinc-200">{t('settings.telegram')}</h2>
                        {isEnv('telegram_token') && <EnvBadge />}
                    </div>

                    <div className="grid gap-2">
                        <div className="flex items-center gap-2">
                            <label htmlFor="token" className="text-sm font-medium text-zinc-400">{t('settings.telegram_token')}</label>
                            <Tooltip content={t('settings.telegram_token_hint')}>
                                <div className="p-1 cursor-help rounded-full hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300">
                                    <Info className="size-4" />
                                </div>
                            </Tooltip>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="grow">
                                <Input
                                    id="token"
                                    value={telegramToken}
                                    onChange={e => { setTelegramToken(e.target.value); }}
                                    placeholder={t('settings.telegram_token_placeholder')}
                                    disabled={isEnv('telegram_token')}
                                    className={isEnv('telegram_token') ? "opacity-60 cursor-not-allowed" : ""}
                                />
                            </div>
                            {isEnv('telegram_token') && <Check className="size-5 text-green-500 shrink-0" />}
                        </div>
                    </div>
                </div>

                <div className="space-y-4 border-t border-zinc-800 pt-6">
                    <h2 className="text-lg font-medium text-zinc-200">{t('settings.torrent_client')}</h2>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <div className="flex items-center gap-2">
                                <label htmlFor="host" className="text-sm font-medium text-zinc-400">{t('settings.host')}</label>
                                {isEnv('qbittorrent_host') && <EnvBadge />}
                            </div>
                            <Input
                                id="host"
                                value={host}
                                onChange={e => { setHost(e.target.value); }}
                                disabled={isEnv('qbittorrent_host')}
                                className={isEnv('qbittorrent_host') ? "opacity-60 cursor-not-allowed" : ""}
                            />
                        </div>
                        <div className="grid gap-2">
                            <div className="flex items-center gap-2">
                                <label htmlFor="port" className="text-sm font-medium text-zinc-400">{t('settings.port')}</label>
                                {isEnv('qbittorrent_port') && <EnvBadge />}
                            </div>
                            <Input
                                id="port"
                                type="number"
                                value={port}
                                onChange={e => { setPort(Number(e.target.value)); }}
                                disabled={isEnv('qbittorrent_port')}
                                className={isEnv('qbittorrent_port') ? "opacity-60 cursor-not-allowed" : ""}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <div className="flex items-center gap-2">
                                <label htmlFor="username" className="text-sm font-medium text-zinc-400">{t('settings.username')}</label>
                                {isEnv('qbittorrent_username') && <EnvBadge />}
                            </div>
                            <Input
                                id="username"
                                value={username}
                                onChange={e => { setUsername(e.target.value); }}
                                disabled={isEnv('qbittorrent_username')}
                                className={isEnv('qbittorrent_username') ? "opacity-60 cursor-not-allowed" : ""}
                            />
                        </div>
                        <div className="grid gap-2">
                            <div className="flex items-center gap-2">
                                <label htmlFor="password" className="text-sm font-medium text-zinc-400">{t('settings.password')}</label>
                                {isEnv('qbittorrent_password') && <EnvBadge />}
                            </div>
                            <Input
                                id="password"
                                type={showTorrentPassword ? "text" : "password"}
                                value={password}
                                onChange={e => { setPassword(e.target.value); }}
                                placeholder={password ? "********" : t('settings.password_placeholder')}
                                disabled={isEnv('qbittorrent_password')}
                                className={isEnv('qbittorrent_password') ? "opacity-60 cursor-not-allowed" : ""}
                                endContent={
                                    <button
                                        type="button"
                                        onClick={() => { setShowTorrentPassword(!showTorrentPassword); }}
                                        className="hover:text-zinc-300 focus:outline-none"
                                    >
                                        {showTorrentPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                                    </button>
                                }
                            />
                        </div>
                    </div>
                </div>

                <div className="space-y-4 border-t border-zinc-800 pt-6">
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-medium text-zinc-200">{t('settings.downloads')}</h2>
                        {isEnv('seed_ratio_limit') && <EnvBadge />}
                    </div>
                    <div className="grid gap-2">
                        <div className="flex items-center gap-2">
                            <label htmlFor="ratio" className="text-sm font-medium text-zinc-400">{t('settings.seed_ratio_limit')}</label>
                            <Tooltip content={t('settings.seed_ratio_limit_hint')}>
                                <div className="p-1 cursor-help rounded-full hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300">
                                    <Info className="size-4" />
                                </div>
                            </Tooltip>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="grow">
                                <Input
                                    id="ratio"
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    value={seedRatioLimit}
                                    onChange={e => { setSeedRatioLimit(Number(e.target.value)); }}
                                    disabled={isEnv('seed_ratio_limit')}
                                    className={isEnv('seed_ratio_limit') ? "opacity-60 cursor-not-allowed" : ""}
                                />
                            </div>
                        </div>
                        <p className="text-xs text-zinc-500">{t('settings.seed_ratio_limit_desc')}</p>
                    </div>

                    <div className="grid gap-2">
                        <div className="flex items-center gap-2">
                            <label htmlFor="timeLimit" className="text-sm font-medium text-zinc-400">{t('settings.seed_time_limit')}</label>
                            {isEnv('seed_time_limit') && <EnvBadge />}
                        </div>
                        <Input
                            id="timeLimit"
                            type="number"
                            min="0"
                            value={seedTimeLimit}
                            onChange={e => { setSeedTimeLimit(Number(e.target.value)); }}
                            disabled={isEnv('seed_time_limit')}
                            className={isEnv('seed_time_limit') ? "opacity-60 cursor-not-allowed" : ""}
                        />
                        <p className="text-xs text-zinc-500">{t('settings.seed_time_limit_desc')}</p>
                    </div>

                    <div className="grid gap-2">
                        <div className="flex items-center gap-2">
                            <label htmlFor="inactiveTimeLimit" className="text-sm font-medium text-zinc-400">{t('settings.inactive_seeding_time_limit')}</label>
                            {isEnv('inactive_seeding_time_limit') && <EnvBadge />}
                        </div>
                        <Input
                            id="inactiveTimeLimit"
                            type="number"
                            min="0"
                            value={inactiveSeedingTimeLimit}
                            onChange={e => { setInactiveSeedingTimeLimit(Number(e.target.value)); }}
                            disabled={isEnv('inactive_seeding_time_limit')}
                            className={isEnv('inactive_seeding_time_limit') ? "opacity-60 cursor-not-allowed" : ""}
                        />
                        <p className="text-xs text-zinc-500">{t('settings.inactive_seeding_time_limit_desc')}</p>
                    </div>
                </div>

                <div className="flex justify-end pt-4">
                    <Button onClick={() => void handleSave()} disabled={saving} className="bg-violet-600 hover:bg-violet-700 text-white px-8">
                        {saving ? t('settings.saving') : t('settings.save_config')}
                    </Button>
                </div>
            </Card>
        </div>
    )
}

const EnvBadge = () => {
    return (
        <span className="inline-flex items-center rounded-full bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 text-xs font-medium text-blue-400">
            ENV
        </span>
    )
}
