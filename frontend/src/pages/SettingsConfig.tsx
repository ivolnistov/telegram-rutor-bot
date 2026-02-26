import { Link } from '@tanstack/react-router'
import {
  checkConfig,
  createTmdbSession,
  getSearchFilters,
  getTmdbAuthUrl,
  saveConfig,
  updateSearchFilters,
  type ConfigSetupRequest,
  type SystemSearchConfig,
} from 'api'
import { Button } from 'components/ui/Button'
import { Card } from 'components/ui/Card'
import { Checkbox } from 'components/ui/Checkbox'
import { Input } from 'components/ui/Input'
import { Select } from 'components/ui/Select'
import { Tooltip } from 'components/ui/Tooltip'
import {
  Check,
  Eye,
  EyeOff,
  Info,
  Pause,
  Settings as SettingsIcon,
  Trash2,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'

export default function SettingsConfig() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [envVars, setEnvVars] = useState<string[]>([])

  const [telegramToken, setTelegramToken] = useState('')
  const [tmdbApiKey, setTmdbApiKey] = useState('')
  const [tmdbSessionId, setTmdbSessionId] = useState('')

  // Torrent Client State
  const [host, setHost] = useState('localhost')
  const [port, setPort] = useState(8080)
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [showTorrentPassword, setShowTorrentPassword] = useState(false)
  const [seedRatioLimit, setSeedRatioLimit] = useState(1)
  const [seedTimeLimit, setSeedTimeLimit] = useState(2880)
  const [inactiveSeedingTimeLimit, setInactiveSeedingTimeLimit] = useState(0)
  const [seedLimitAction, setSeedLimitAction] = useState(0)

  // Search Filters
  const [qualityFilters, setQualityFilters] = useState('')
  const [translationFilters, setTranslationFilters] = useState('')

  // Active System Searches
  const [activeSearches, setActiveSearches] = useState<SystemSearchConfig[]>([])

  const handleConnectTmdb = async () => {
    try {
      // Ensure key is saved to backend before requesting token
      await handleSave()
      const { auth_url } = await getTmdbAuthUrl(globalThis.location.href)
      globalThis.location.href = auth_url
    } catch (e) {
      console.error(e)
      toast.error('Failed to get TMDB auth URL (Ensure API Key is valid)')
    }
  }

  const processedToken = useRef<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(globalThis.location.search)
    const requestToken = params.get('request_token')
    const approved = params.get('approved')

    if (requestToken && approved === 'true') {
      // Prevent double invocation (React Strict Mode)
      if (processedToken.current === requestToken) {
        return
      }
      processedToken.current = requestToken

      const finishAuth = async () => {
        const toastId = toast.loading('Connecting to TMDB...')
        try {
          await createTmdbSession(requestToken)
          toast.dismiss(toastId)
          toast.success('Connected to TMDB!')

          // Clear URL
          globalThis.history.replaceState({}, '', globalThis.location.pathname)

          // Refresh config
          const res = await checkConfig()
          setTmdbSessionId(String(res.current_values.tmdb_session_id || ''))
        } catch (e) {
          console.error(e)
          toast.dismiss(toastId)
          toast.error('Failed to create TMDB session')
        }
      }

      void finishAuth()
    }
  }, [])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await checkConfig()
        setTelegramToken(String(res.current_values.telegram_token || ''))
        setTmdbApiKey(String(res.current_values.tmdb_api_key || ''))
        setTmdbSessionId(String(res.current_values.tmdb_session_id || ''))

        setHost(String(res.current_values.qbittorrent_host || 'localhost'))
        setPort(Number(res.current_values.qbittorrent_port || 8080))
        setUsername(String(res.current_values.qbittorrent_username || 'admin'))
        setPassword(String(res.current_values.qbittorrent_password || ''))

        setSeedRatioLimit(Number(res.current_values.seed_ratio_limit || 1))
        setSeedTimeLimit(Number(res.current_values.seed_time_limit || 2880))
        setSeedLimitAction(Number(res.current_values.seed_limit_action || 0))
        setEnvVars(res.env_vars)
        if (res.searches) {
          setActiveSearches(res.searches)
        } else if (res.current_values.searches) {
          setActiveSearches(res.current_values.searches)
        }

        // Load Filters
        const filters = await getSearchFilters()
        setQualityFilters(filters.quality || '')
        setTranslationFilters(filters.translation || '')
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
      tmdb_api_key: tmdbApiKey,
      tmdb_session_id: tmdbSessionId,
      torrent: {
        client: 'qbittorrent',
        host,
        port: port,
        username,
        password,
      },
      seed_ratio_limit: seedRatioLimit,
      seed_time_limit: seedTimeLimit,
      inactive_seeding_time_limit: inactiveSeedingTimeLimit,
      seed_limit_action: seedLimitAction,
    }

    try {
      await saveConfig(config)
      await updateSearchFilters({
        quality: qualityFilters || null,
        translation: translationFilters || null,
      })
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
          <p className="text-zinc-500 text-sm mt-1">
            {t('settings.description')}
          </p>
        </div>
      </div>

      <Card className="p-6 space-y-8">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-medium text-zinc-200">
              {t('settings.telegram')}
            </h2>
            {isEnv('telegram_token') && <EnvBadge />}
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label
                htmlFor="token"
                className="text-sm font-medium text-zinc-400"
              >
                {t('settings.telegram_token')}
              </label>
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
                  onChange={(e) => {
                    setTelegramToken(e.target.value)
                  }}
                  placeholder={t('settings.telegram_token_placeholder')}
                  disabled={isEnv('telegram_token')}
                  className={
                    isEnv('telegram_token')
                      ? 'opacity-60 cursor-not-allowed'
                      : ''
                  }
                />
              </div>
              {isEnv('telegram_token') && (
                <Check className="size-5 text-green-500 shrink-0" />
              )}
            </div>
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label
                htmlFor="tmdbApiKey"
                className="text-sm font-medium text-zinc-400"
              >
                {t('settings.tmdb_api_key')}
              </label>
              <Tooltip
                content={
                  <>
                    {t('settings.tmdb_api_key_hint')}{' '}
                    <a
                      href="https://www.themoviedb.org/settings/api"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-400 hover:underline"
                    >
                      Are you lost? Get API Key here.
                    </a>
                  </>
                }
              >
                <div className="p-1 cursor-help rounded-full hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300">
                  <Info className="size-4" />
                </div>
              </Tooltip>
            </div>
            <div className="flex items-center gap-2">
              <div className="grow">
                <Input
                  id="tmdbApiKey"
                  type="password"
                  value={tmdbApiKey}
                  onChange={(e) => {
                    setTmdbApiKey(e.target.value)
                  }}
                  placeholder={t('settings.tmdb_api_key_placeholder')}
                />
              </div>
            </div>
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label
                htmlFor="tmdbSessionId"
                className="text-sm font-medium text-zinc-400"
              >
                {t('settings.tmdb_session_id')}
              </label>
              <Tooltip content={t('settings.tmdb_session_id_hint')}>
                <div className="p-1 cursor-help rounded-full hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300">
                  <Info className="size-4" />
                </div>
              </Tooltip>
            </div>
            <div className="flex items-center gap-2">
              <div className="grow">
                <Input
                  id="tmdbSessionId"
                  type="password"
                  value={tmdbSessionId}
                  onChange={(e) => {
                    setTmdbSessionId(e.target.value)
                  }}
                  placeholder={t('settings.tmdb_session_id_placeholder')}
                />
              </div>
              {tmdbApiKey && !tmdbSessionId && (
                <Button
                  variant="outline"
                  onClick={() => {
                    void handleConnectTmdb()
                  }}
                  className="shrink-0"
                >
                  Connect TMDB
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4 border-t border-zinc-800 pt-6">
          <h2 className="text-lg font-medium text-zinc-200">
            {t('settings.torrent_client')}
          </h2>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="host"
                  className="text-sm font-medium text-zinc-400"
                >
                  {t('settings.host')}
                </label>
                {isEnv('qbittorrent_host') && <EnvBadge />}
              </div>
              <Input
                id="host"
                value={host}
                onChange={(e) => {
                  setHost(e.target.value)
                }}
                disabled={isEnv('qbittorrent_host')}
                className={
                  isEnv('qbittorrent_host')
                    ? 'opacity-60 cursor-not-allowed'
                    : ''
                }
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="port"
                  className="text-sm font-medium text-zinc-400"
                >
                  {t('settings.port')}
                </label>
                {isEnv('qbittorrent_port') && <EnvBadge />}
              </div>
              <Input
                id="port"
                type="number"
                value={port}
                onChange={(e) => {
                  setPort(Number(e.target.value))
                }}
                disabled={isEnv('qbittorrent_port')}
                className={
                  isEnv('qbittorrent_port')
                    ? 'opacity-60 cursor-not-allowed'
                    : ''
                }
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="username"
                  className="text-sm font-medium text-zinc-400"
                >
                  {t('settings.username')}
                </label>
                {isEnv('qbittorrent_username') && <EnvBadge />}
              </div>
              <Input
                id="username"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value)
                }}
                disabled={isEnv('qbittorrent_username')}
                className={
                  isEnv('qbittorrent_username')
                    ? 'opacity-60 cursor-not-allowed'
                    : ''
                }
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="password"
                  className="text-sm font-medium text-zinc-400"
                >
                  {t('settings.password')}
                </label>
                {isEnv('qbittorrent_password') && <EnvBadge />}
              </div>
              <Input
                id="password"
                type={showTorrentPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                }}
                placeholder={
                  password ? '********' : t('settings.password_placeholder')
                }
                disabled={isEnv('qbittorrent_password')}
                className={
                  isEnv('qbittorrent_password')
                    ? 'opacity-60 cursor-not-allowed'
                    : ''
                }
                endContent={
                  <button
                    type="button"
                    onClick={() => {
                      setShowTorrentPassword(!showTorrentPassword)
                    }}
                    className="hover:text-zinc-300 focus:outline-none"
                  >
                    {showTorrentPassword ? (
                      <EyeOff className="size-4" />
                    ) : (
                      <Eye className="size-4" />
                    )}
                  </button>
                }
              />
            </div>
          </div>
        </div>

        <div className="space-y-4 border-t border-zinc-800 pt-6">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-medium text-zinc-200">
              {t('settings.downloads')}
            </h2>
            {isEnv('seed_ratio_limit') && <EnvBadge />}
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-zinc-400">
                {t('settings.seed_limit_action')}
              </label>
            </div>
            <Select
              value={seedLimitAction}
              onChange={(val) => {
                setSeedLimitAction(Number(val))
              }}
              options={[
                {
                  value: 0,
                  label: t('settings.action_pause'),
                  icon: <Pause className="size-3.5 text-yellow-500" />,
                },
                {
                  value: 1,
                  label: t('settings.action_remove'),
                  icon: <Trash2 className="size-3.5 text-red-500" />,
                },
              ]}
            />
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label
                htmlFor="ratio"
                className="text-sm font-medium text-zinc-400"
              >
                {t('settings.seed_ratio_limit')}
              </label>
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
                  onChange={(e) => {
                    setSeedRatioLimit(Number(e.target.value))
                  }}
                  disabled={isEnv('seed_ratio_limit')}
                  className={
                    isEnv('seed_ratio_limit')
                      ? 'opacity-60 cursor-not-allowed'
                      : ''
                  }
                />
              </div>
            </div>
            <p className="text-xs text-zinc-500">
              {t('settings.seed_ratio_limit_desc')}
            </p>
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label
                htmlFor="timeLimit"
                className="text-sm font-medium text-zinc-400"
              >
                {t('settings.seed_time_limit')}
              </label>
              {isEnv('seed_time_limit') && <EnvBadge />}
            </div>
            <Input
              id="timeLimit"
              type="number"
              min="0"
              value={seedTimeLimit}
              onChange={(e) => {
                setSeedTimeLimit(Number(e.target.value))
              }}
              disabled={isEnv('seed_time_limit')}
              className={
                isEnv('seed_time_limit') ? 'opacity-60 cursor-not-allowed' : ''
              }
            />
            <p className="text-xs text-zinc-500">
              {t('settings.seed_time_limit_desc')}
            </p>
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label
                htmlFor="inactiveTimeLimit"
                className="text-sm font-medium text-zinc-400"
              >
                {t('settings.inactive_seeding_time_limit')}
              </label>
              {isEnv('inactive_seeding_time_limit') && <EnvBadge />}
            </div>
            <Input
              id="inactiveTimeLimit"
              type="number"
              min="0"
              value={inactiveSeedingTimeLimit}
              onChange={(e) => {
                setInactiveSeedingTimeLimit(Number(e.target.value))
              }}
              disabled={isEnv('inactive_seeding_time_limit')}
              className={
                isEnv('inactive_seeding_time_limit')
                  ? 'opacity-60 cursor-not-allowed'
                  : ''
              }
            />
            <p className="text-xs text-zinc-500">
              {t('settings.inactive_seeding_time_limit_desc')}
            </p>
          </div>
        </div>

        <div className="space-y-4 border-t border-zinc-800 pt-6">
          <h2 className="text-lg font-medium text-zinc-200">Search Filters</h2>
          <div className="grid gap-2">
            <label
              htmlFor="qualityFilters"
              className="text-sm font-medium text-zinc-400"
            >
              Quality Filters (comma separated, e.g. 1080p, 2160p)
            </label>
            <Input
              id="qualityFilters"
              value={qualityFilters}
              onChange={(e) => {
                setQualityFilters(e.target.value)
              }}
              placeholder="e.g. 1080p, 2160p, HDR"
            />
            <p className="text-xs text-zinc-500">
              Only torrents containing these keywords will be
              notified/downloaded. Leave empty for all.
            </p>
          </div>
          <div className="grid gap-2">
            <label
              htmlFor="translationFilters"
              className="text-sm font-medium text-zinc-400"
            >
              Translation Filters (comma separated, e.g. Dubbed, MVO)
            </label>
            <Input
              id="translationFilters"
              value={translationFilters}
              onChange={(e) => {
                setTranslationFilters(e.target.value)
              }}
              placeholder="e.g. Dubbed, MVO, Original"
            />
            <p className="text-xs text-zinc-500">
              Only torrents matching these translations will be
              notified/downloaded.
            </p>
          </div>
        </div>

        <div className="space-y-4 border-t border-zinc-800 pt-6">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-medium text-zinc-200">
              Active Searches (System)
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setActiveSearches([
                  ...activeSearches,
                  {
                    name: '',
                    url: '',
                    cron: '0 * * * *',
                    category: '',
                    is_series: false,
                  },
                ])
              }}
            >
              Add Search
            </Button>
          </div>
          <p className="text-xs text-zinc-500 mb-4">
            These searches run automatically in the background. Use {'{year}'}{' '}
            in the URL for dynamic substitution.
          </p>

          <div className="space-y-4">
            {activeSearches.map((search, index) => (
              <div
                key={search.url || index}
                className="grid grid-cols-1 md:grid-cols-[1fr_2fr_1fr_1fr_auto_auto] gap-3 items-start bg-zinc-900/50 p-3 rounded-lg border border-zinc-800"
              >
                <div>
                  <label
                    htmlFor={`search-name-${String(index)}`}
                    className="text-xs font-medium text-zinc-500 mb-1 block"
                  >
                    Name
                  </label>
                  <Input
                    id={`search-name-${String(index)}`}
                    value={search.name}
                    onChange={(e) => {
                      const newSearches = [...activeSearches]
                      newSearches[index].name = e.target.value
                      setActiveSearches(newSearches)
                    }}
                    placeholder="e.g. Top Movies {year}"
                  />
                </div>
                <div>
                  <label
                    htmlFor={`search-url-${String(index)}`}
                    className="text-xs font-medium text-zinc-500 mb-1 block"
                  >
                    Rutor URL
                  </label>
                  <Input
                    id={`search-url-${String(index)}`}
                    value={search.url}
                    onChange={(e) => {
                      const newSearches = [...activeSearches]
                      newSearches[index].url = e.target.value
                      setActiveSearches(newSearches)
                    }}
                    placeholder="http://rutor.info/search/0/0/000/0/{year}"
                  />
                </div>
                <div>
                  <label
                    htmlFor={`search-cron-${String(index)}`}
                    className="text-xs font-medium text-zinc-500 mb-1 block"
                  >
                    Cron Schedule
                  </label>
                  <Input
                    id={`search-cron-${String(index)}`}
                    value={search.cron}
                    onChange={(e) => {
                      const newSearches = [...activeSearches]
                      newSearches[index].cron = e.target.value
                      setActiveSearches(newSearches)
                    }}
                    placeholder="0 * * * *"
                  />
                </div>
                <div>
                  <label
                    htmlFor={`search-cat-${String(index)}`}
                    className="text-xs font-medium text-zinc-500 mb-1 block"
                  >
                    Category
                  </label>
                  <Input
                    id={`search-cat-${String(index)}`}
                    value={search.category || ''}
                    onChange={(e) => {
                      const newSearches = [...activeSearches]
                      newSearches[index].category = e.target.value
                      setActiveSearches(newSearches)
                    }}
                    placeholder="qbittorrent cat"
                  />
                </div>
                <div className="flex flex-col items-center justify-center pt-2">
                  <label
                    htmlFor={`search-series-${String(index)}`}
                    className="text-xs font-medium text-zinc-500 mb-2 block"
                  >
                    Сериалы
                  </label>
                  <Checkbox
                    id={`search-series-${String(index)}`}
                    checked={search.is_series || false}
                    onCheckedChange={(checked) => {
                      const newSearches = [...activeSearches]
                      newSearches[index].is_series = checked
                      setActiveSearches(newSearches)
                    }}
                  />
                </div>
                <div className="flex items-end justify-center h-full pt-6">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                    onClick={() => {
                      const newSearches = [...activeSearches]
                      newSearches.splice(index, 1)
                      setActiveSearches(newSearches)
                    }}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
            {activeSearches.length === 0 && (
              <div className="text-center py-8 text-sm text-zinc-500 italic bg-zinc-900/30 rounded-lg border border-dashed border-zinc-800">
                No active system searches configured.
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <Button
            onClick={() => {
              void handleSave()
            }}
            disabled={saving}
            className="bg-violet-600 hover:bg-violet-700 text-white px-8"
          >
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
