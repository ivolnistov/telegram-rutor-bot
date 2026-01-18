import axios from 'axios'
import type { Category, Film, Search, TaskExecution, Torrent, User, Download } from './types'

const api = axios.create({
    baseURL: '/api'
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
                if (!window.location.pathname.startsWith('/login')) {
                    window.location.href = '/login'
                }
            }
        }
        return Promise.reject(error instanceof Error ? error : new Error(String(error)))
    }
)

export const getSearches = async (): Promise<Search[]> => (await api.get('/searches')).data as Search[]
export const createSearch = async (formData: FormData): Promise<Search> => (await api.post('/searches', formData)).data as Search
export const updateSearch = async ({ id, url, cron, category }: { id: number | string, url?: string, cron?: string, category?: string }): Promise<Search> => {
    const formData = new FormData()
    if (url) formData.append('url', url)
    if (cron) formData.append('cron', cron)
    if (category !== undefined) formData.append('category', category)
    return (await api.patch(`/searches/${String(id)}`, formData)).data as Search
}
export const deleteSearch = async (id: number | string): Promise<unknown> => (await api.delete(`/searches/${String(id)}`)).data
export const executeSearch = async (id: number | string, chatId: number | string): Promise<unknown> => {
    const formData = new FormData()
    formData.append('chat_id', String(chatId))
    return (await api.post(`/searches/${String(id)}/execute`, formData)).data
}

export const getSearchSubscribers = async (id: number | string): Promise<User[]> => (await api.get(`/searches/${String(id)}/subscribers`)).data as User[]
export const addSearchSubscriber = async (id: number | string, chatId: number | string): Promise<unknown> => {
    const formData = new FormData()
    formData.append('chat_id', String(chatId))
    return (await api.post(`/searches/${String(id)}/subscribers`, formData)).data
}
export const removeSearchSubscriber = async (id: number | string, userId: number | string): Promise<unknown> => (await api.delete(`/searches/${String(id)}/subscribers/${String(userId)}`)).data

export const getTorrents = async (limit: number = 50): Promise<Torrent[]> => (await api.get(`/torrents?limit=${String(limit)}`)).data as Torrent[]
export const downloadTorrent = async (id: number | string): Promise<unknown> => (await api.post(`/torrents/${String(id)}/download`)).data
export const deleteTorrent = async (id: number | string): Promise<unknown> => (await api.delete(`/torrents/${String(id)}`)).data

export const getFilms = async (query: string = '', categoryId?: number | string, limit: number = 50): Promise<Film[]> => {
    const params = new URLSearchParams()
    if (query) params.append('q', query)
    if (categoryId) params.append('category_id', String(categoryId))
    params.append('limit', String(limit))
    return (await api.get(`/films?${params.toString()}`)).data as Film[]
}
export const getCategories = async (): Promise<Category[]> => (await api.get('/categories')).data as Category[]
export const createCategory = async (formData: FormData): Promise<Category> => (await api.post('/categories', formData)).data as Category
export const updateCategory = async ({ id, ...data }: { id: number | string, name?: string, icon?: string, folder?: string, active?: boolean }): Promise<Category> => {
    const formData = new FormData()
    if (data.name) formData.append('name', data.name)
    if (data.icon) formData.append('icon', data.icon)
    if (data.folder) formData.append('folder', data.folder)
    if (data.active !== undefined) formData.append('active', String(data.active))
    return (await api.patch(`/categories/${String(id)}`, formData)).data as Category
}
export const deleteCategory = async (id: number | string): Promise<unknown> => (await api.delete(`/categories/${String(id)}`)).data

export const getUsers = async (): Promise<User[]> => (await api.get('/users')).data as User[]

export const updateUserStatus = async ({ id, is_authorized, is_admin, is_tfa_enabled, password, language }: { id: number | string, is_authorized?: boolean, is_admin?: boolean, is_tfa_enabled?: boolean, password?: string, language?: string }): Promise<User> => {
    const formData = new FormData()
    if (is_authorized !== undefined) formData.append('is_authorized', String(is_authorized))
    if (is_admin !== undefined) formData.append('is_admin', String(is_admin))
    if (is_tfa_enabled !== undefined) formData.append('is_tfa_enabled', String(is_tfa_enabled))
    if (password !== undefined) formData.append('password', password)
    if (language !== undefined) formData.append('language', language)
    return (await api.patch(`/users/${String(id)}/status`, formData)).data as User
}

// Config API
export interface ConfigCheckResponse {
    configured: boolean
    missing_fields: string[]
    current_values: Record<string, string | number | boolean | null>
    env_vars: string[]
}

export interface TorrentConfig {
    client: "qbittorrent" | "transmission"
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
    seed_ratio_limit?: number
    seed_time_limit?: number
    inactive_seeding_time_limit?: number
}


export const checkConfig = async (): Promise<ConfigCheckResponse> => (await api.get('/config')).data as ConfigCheckResponse

export const saveConfig = async (config: ConfigSetupRequest): Promise<ConfigCheckResponse> => (await api.post('/config', config)).data as ConfigCheckResponse

export interface AuthResponse {
    access_token?: string
    token_type?: string
    tfa_required?: boolean
    username?: string
}

export const login = async (username: string, password: string): Promise<AuthResponse> => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return (await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })).data as AuthResponse
}

export const verifyTfa = async (username: string, code: string): Promise<AuthResponse> => {
    return (await api.post('/auth/verify-tfa', { username, code })).data as AuthResponse
}

export const getMe = async (): Promise<User> => (await api.get('/auth/me')).data as User

export const getTasks = async (limit: number = 50): Promise<TaskExecution[]> => (await api.get(`/tasks?limit=${String(limit)}`)).data as TaskExecution[]
export const getDownloads = async (): Promise<Download[]> => (await api.get('/downloads')).data as Download[]
export const deleteDownload = async (hash: string): Promise<void> => { await api.delete(`/downloads/${hash}`) }
