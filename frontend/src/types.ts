export interface Category {
    id: number
    name: string
    icon?: string | null
    folder?: string | null
    active: boolean
}

export interface User {
    id: number
    chat_id: number
    name?: string | null
    username?: string | null
    password?: string | null
    is_authorized: boolean
    is_admin: boolean
    is_tfa_enabled: boolean
    language: string
}

export interface Torrent {
    id: number
    film_id: number
    blake: string
    name: string
    magnet: string
    created: string // date string
    link: string
    sz: number
    approved: boolean
    downloaded: boolean
    seeds?: number | null
    date?: string | null
}

export interface Film {
    id: number
    blake: string
    year: number
    name: string
    ru_name?: string | null
    poster?: string | null
    rating?: string | null
    country?: string | null
    genres?: string | null
    category_id?: number | null
    torrents: Torrent[]
}

export interface Search {
    id: number
    url: string
    cron: string
    last_success?: string | null
    creator_id?: number | null
    query?: string | null
    category?: string | null // category name, fetched as property or field? Property 'category' was added to Search model as string name.
    category_id?: number | null
}

export interface TaskExecution {
    id: number
    search_id: number
    status: string
    start_time: string
    end_time?: string | null
    result?: string | null
    progress: number
    search?: Search | null
}

export interface Download {
    id: string
    name: string
    hash: string
    size: number
    progress: number
    status: string
    download_rate: number
    upload_rate: number
    download_dir?: string | null
    magnet_uri: string
    seeds?: number
    peers?: number
}
