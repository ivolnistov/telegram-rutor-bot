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
  film?: Film | null
}

export interface RutorTorrent {
  name: string
  size: number
  date: string
  magnet: string
  link: string
  year: string
}

export interface Film {
  id: number
  blake: string
  year: number
  name: string
  ru_name?: string | null
  poster?: string | null
  rating?: string | null
  user_rating?: number | null
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
  category?: string | null
  category_id?: number | null
  quality_filters?: string | null
  translation_filters?: string | null
  is_series?: boolean
}
export interface TmdbMedia {
  id: number
  original_title?: string
  original_name?: string
  title?: string // Movies
  name?: string // TV Shows
  poster_path: string | null
  backdrop_path: string | null
  overview: string
  media_type: 'movie' | 'tv' | 'person'
  release_date?: string
  first_air_date?: string
  vote_average: number
  in_library?: boolean
  torrents_count?: number
  kp_rating?: number
  genres?: { id: number; name: string }[]
  production_countries?: { iso_3166_1: string; name: string }[]
  external_ids?: {
    imdb_id?: string
    facebook_id?: string
    instagram_id?: string
    twitter_id?: string
  }
  imdb_id?: string // Shortcut or computed
  runtime?: number
  origin_country?: string[]
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
