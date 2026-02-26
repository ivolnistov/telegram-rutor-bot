import axios from 'axios'
import type {
  Category,
  Download,
  Film,
  Search,
  TaskExecution,
  TmdbMedia,
  Torrent,
  User,
} from './types'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        if (!globalThis.location.pathname.startsWith('/login')) {
          globalThis.location.href = '/login'
        }
      }
    }
    return Promise.reject(
      error instanceof Error ? error : new Error(String(error)),
    )
  },
)

export const getSearches = async (): Promise<Search[]> =>
  (await api.get('/searches')).data as unknown as Search[]
export const createSearch = async (formData: FormData): Promise<Search> =>
  (await api.post('/searches', formData)).data as unknown as Search
export const updateSearch = async ({
  id,
  url,
  cron,
  category,
}: {
  id: number | string
  url?: string
  cron?: string
  category?: string
}): Promise<Search> => {
  const formData = new FormData()
  if (url) formData.append('url', url)
  if (cron) formData.append('cron', cron)
  if (category !== undefined) formData.append('category', category)
  return (await api.patch(`/searches/${String(id)}`, formData))
    .data as unknown as Search
}
export const deleteSearch = async (id: number | string): Promise<unknown> =>
  (await api.delete(`/searches/${String(id)}`)).data
export const executeSearch = async (
  id: number | string,
  chatId: number | string,
  notify: boolean = true,
): Promise<unknown> => {
  const formData = new FormData()
  formData.append('chat_id', String(chatId))
  formData.append('notify', String(notify))
  return (await api.post(`/searches/${String(id)}/execute`, formData)).data
}

export const getSearchSubscribers = async (
  id: number | string,
): Promise<User[]> =>
  (await api.get(`/searches/${String(id)}/subscribers`))
    .data as unknown as User[]
export const addSearchSubscriber = async (
  id: number | string,
  chatId: number | string,
): Promise<unknown> => {
  const formData = new FormData()
  formData.append('chat_id', String(chatId))
  return (await api.post(`/searches/${String(id)}/subscribers`, formData)).data
}
export const removeSearchSubscriber = async (
  id: number | string,
  userId: number | string,
): Promise<unknown> =>
  (await api.delete(`/searches/${String(id)}/subscribers/${String(userId)}`))
    .data

export const getTorrents = async (
  limit: number = 50,
  query?: string,
): Promise<Torrent[]> => {
  const params = new URLSearchParams()
  params.append('limit', String(limit))
  if (query) params.append('q', query)
  return (await api.get(`/torrents?${params.toString()}`))
    .data as unknown as Torrent[]
}
export const downloadTorrent = async (id: number | string): Promise<unknown> =>
  (await api.post(`/torrents/${String(id)}/download`)).data
export const deleteTorrent = async (id: number | string): Promise<unknown> =>
  (await api.delete(`/torrents/${String(id)}`)).data

export const searchFilmTorrents = async (
  filmId: number,
  query?: string,
): Promise<{ status: string }> =>
  (
    await api.post(`/films/${String(filmId)}/search`, null, {
      params: { query },
    })
  ).data as { status: string }

export const searchOnRutor = async (
  mediaType: string,
  mediaId: number,
): Promise<{ status: string }> =>
  (
    await api.post('/discovery/search_on_rutor', null, {
      params: { media_type: mediaType, media_id: String(mediaId) },
    })
  ).data as { status: string }

export const getFilms = async (
  query: string = '',
  categoryId?: number | string,
  limit: number = 50,
): Promise<Film[]> => {
  const params = new URLSearchParams()
  if (query) params.append('q', query)
  if (categoryId) params.append('category_id', String(categoryId))
  params.append('limit', String(limit))
  return (await api.get(`/films?${params.toString()}`))
    .data as unknown as Film[]
}
export const updateFilm = async (
  id: number,
  film: Partial<Film>,
): Promise<unknown> => {
  const formData = new FormData()
  if (film.user_rating !== undefined) {
    formData.append('user_rating', String(film.user_rating))
  }
  return (await api.put(`/films/${String(id)}`, formData)).data
}
export const getCategories = async (): Promise<Category[]> =>
  (await api.get('/categories')).data as unknown as Category[]
export const createCategory = async (formData: FormData): Promise<Category> =>
  (await api.post('/categories', formData)).data as unknown as Category
export const updateCategory = async ({
  id,
  ...data
}: {
  id: number | string
  name?: string
  icon?: string
  folder?: string
  active?: boolean
}): Promise<Category> => {
  const formData = new FormData()
  if (data.name) formData.append('name', data.name)
  if (data.icon) formData.append('icon', data.icon)
  if (data.folder) formData.append('folder', data.folder)
  if (data.active !== undefined) formData.append('active', String(data.active))
  return (await api.patch(`/categories/${String(id)}`, formData))
    .data as unknown as Category
}
export const deleteCategory = async (id: number | string): Promise<unknown> =>
  (await api.delete(`/categories/${String(id)}`)).data

export const getUsers = async (): Promise<User[]> =>
  (await api.get('/users')).data as unknown as User[]

export const updateUserStatus = async ({
  id,
  is_authorized,
  is_admin,
  is_tfa_enabled,
  password,
  language,
}: {
  id: number | string
  is_authorized?: boolean
  is_admin?: boolean
  is_tfa_enabled?: boolean
  password?: string
  language?: string
}): Promise<User> => {
  const formData = new FormData()
  if (is_authorized !== undefined)
    formData.append('is_authorized', String(is_authorized))
  if (is_admin !== undefined) formData.append('is_admin', String(is_admin))
  if (is_tfa_enabled !== undefined)
    formData.append('is_tfa_enabled', String(is_tfa_enabled))
  if (password !== undefined) formData.append('password', password)
  if (language !== undefined) formData.append('language', language)
  return (await api.patch(`/users/${String(id)}/status`, formData))
    .data as unknown as User
}

// Config API
export interface SystemSearchConfig {
  name: string
  url: string
  cron: string
  category?: string
  is_series?: boolean
}

export interface ConfigCheckResponse {
  configured: boolean
  missing_fields: string[]
  current_values: Record<string, string | number | boolean | null> & {
    searches?: SystemSearchConfig[]
  }
  env_vars: string[]
  searches?: SystemSearchConfig[]
}

export interface TorrentConfig {
  client: 'qbittorrent' | 'transmission'
  host: string
  port: number
  username: string
  password: string
}

export interface UserConfig {
  id: number
  username?: string
  password?: string
  is_tfa_enabled?: boolean
  language?: string
}

export interface TelegramConfig {
  token: string
  initial_users?: UserConfig[]
}

export interface ConfigSetupRequest {
  telegram: TelegramConfig
  torrent: TorrentConfig
  tmdb_api_key?: string
  tmdb_session_id?: string
  seed_ratio_limit?: number
  seed_time_limit?: number
  inactive_seeding_time_limit?: number
  seed_limit_action?: number
}

export const checkConfig = async (): Promise<ConfigCheckResponse> =>
  (await api.get('/config')).data as unknown as ConfigCheckResponse

export const saveConfig = async (
  config: ConfigSetupRequest,
): Promise<ConfigCheckResponse> =>
  (await api.post('/config', config)).data as unknown as ConfigCheckResponse

export interface AuthResponse {
  access_token?: string
  token_type?: string
  tfa_required?: boolean
  username?: string
}

export const login = async (
  username: string,
  password: string,
): Promise<AuthResponse> => {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  return (
    await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  ).data as unknown as AuthResponse
}

export const verifyTfa = async (
  username: string,
  code: string,
): Promise<AuthResponse> => {
  return (await api.post('/auth/verify-tfa', { username, code }))
    .data as unknown as AuthResponse
}

export const getMe = async (): Promise<User> =>
  (await api.get('/auth/me')).data as unknown as User

export const getTasks = async (limit: number = 50): Promise<TaskExecution[]> =>
  (await api.get(`/tasks?limit=${String(limit)}`))
    .data as unknown as TaskExecution[]
export const getDownloads = async (): Promise<Download[]> =>
  (await api.get('/downloads')).data as unknown as Download[]
export const deleteDownload = async (hash: string): Promise<void> => {
  await api.delete(`/downloads/${hash}`)
}

export const getTrending = async (
  mediaType: 'all' | 'movie' | 'tv' = 'all',
  timeWindow: 'day' | 'week' = 'week',
): Promise<TmdbMedia[]> =>
  (
    await api.get(
      `/discovery/trending?media_type=${mediaType}&time_window=${timeWindow}`,
    )
  ).data as unknown as TmdbMedia[]

export const searchDiscovery = async (query: string): Promise<TmdbMedia[]> =>
  (await api.get(`/discovery/search?q=${encodeURIComponent(query)}`))
    .data as unknown as TmdbMedia[]

export const getRecommendations = async (
  mediaType: 'movie' | 'tv',
  mediaId: number,
): Promise<TmdbMedia[]> =>
  (await api.get(`/discovery/${mediaType}/${String(mediaId)}/recommendations`))
    .data as unknown as TmdbMedia[]

export const getPersonalRecommendations = async (): Promise<TmdbMedia[]> =>
  (await api.get('/discovery/personal')).data as unknown as TmdbMedia[]

export const getMediaDetails = async (
  mediaType: 'movie' | 'tv' | 'person',
  mediaId: number,
): Promise<TmdbMedia> =>
  (await api.get(`/discovery/${mediaType}/${String(mediaId)}`))
    .data as unknown as TmdbMedia

export const getLibrary = async (
  mediaType: 'movie' | 'tv',
  page = 1,
): Promise<TmdbMedia[]> => {
  const limit = 20
  const offset = (page - 1) * limit
  return (
    await api.get(
      `/discovery/library?media_type=${mediaType}&limit=${String(limit)}&offset=${String(offset)}`,
    )
  ).data as unknown as TmdbMedia[]
}

export const rateMedia = async (
  mediaType: 'movie' | 'tv',
  mediaId: number,
  value: number,
): Promise<unknown> =>
  (
    await api.post('/discovery/rate', {
      media_type: mediaType,
      media_id: mediaId,
      value,
    })
  ).data as { status: string }

export const deleteRating = async (
  mediaType: 'movie' | 'tv',
  mediaId: number,
): Promise<unknown> =>
  (
    await api.delete(
      `/discovery/rate?media_type=${mediaType}&media_id=${String(mediaId)}`,
    )
  ).data as { status: string }

export const getRatedMedia = async (
  mediaType: 'movie' | 'tv',
): Promise<TmdbMedia[]> =>
  (await api.get(`/discovery/rated?media_type=${mediaType}`))
    .data as unknown as TmdbMedia[]

export const getMediaAccountStates = async (
  mediaType: 'movie' | 'tv',
  mediaId: number,
): Promise<{
  rated: { value: number } | boolean
  favorite: boolean
  watchlist: boolean
  in_library?: boolean
}> =>
  (await api.get(`/discovery/${mediaType}/${String(mediaId)}/account_states`))
    .data as {
    rated: { value: number } | boolean
    favorite: boolean
    watchlist: boolean
    in_library?: boolean
  }

export const getMediaTorrents = async (
  mediaType: 'movie' | 'tv',
  mediaId: number,
): Promise<Torrent[]> =>
  (await api.get(`/discovery/${mediaType}/${String(mediaId)}/torrents`))
    .data as unknown as Torrent[]

export const getTmdbAuthUrl = async (
  redirectTo: string,
): Promise<{ auth_url: string }> =>
  (
    await api.get(
      `/config/tmdb/auth-url?redirect_to=${encodeURIComponent(redirectTo)}`,
    )
  ).data as { auth_url: string }

export const createTmdbSession = async (
  requestToken: string,
): Promise<ConfigCheckResponse> =>
  (await api.post('/config/tmdb/session', { request_token: requestToken }))
    .data as unknown as ConfigCheckResponse

export const syncLibrary = async (): Promise<{ matched: number }> =>
  (await api.post('/discovery/sync')).data as { matched: number }

export const getWatchlist = async (mediaType: string): Promise<TmdbMedia[]> =>
  (await api.get('/discovery/watchlist', { params: { media_type: mediaType } }))
    .data as TmdbMedia[]

export const addToWatchlist = async (
  mediaType: string,
  mediaId: number,
  watchlist: boolean = true,
): Promise<void> => {
  await api.post('/discovery/watchlist', null, {
    params: { media_type: mediaType, media_id: mediaId, watchlist },
  })
}

export const syncWatchlist = async (): Promise<{
  status: string
  synced: number
}> =>
  (await api.post('/discovery/watchlist/sync')).data as {
    status: string
    synced: number
  }

export const getSearchFilters = async (): Promise<{
  quality: string | null
  translation: string | null
}> =>
  (await api.get('/config/filters')).data as {
    quality: string | null
    translation: string | null
  }

export const updateSearchFilters = async (filters: {
  quality: string | null
  translation: string | null
}): Promise<void> => {
  await api.post('/config/filters', filters)
}
