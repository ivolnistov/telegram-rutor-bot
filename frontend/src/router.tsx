import {
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'
import App from './App'
import LibraryPage from './pages/Library'
import SettingsCategory from './pages/SettingsCategory'
import SettingsConfig from './pages/SettingsConfig'
import SettingsUsers from './pages/SettingsUsers'

const rootRoute = createRootRoute({
  component: App,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DiscoveryPage,
})

const libraryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/library',
  component: LibraryPage,
})

import DiscoveryPage from './pages/Discovery'

const discoveryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: DiscoveryPage,
})

const settingsCategoryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings/category',
  component: SettingsCategory,
})

const settingsUsersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings/users',
  component: SettingsUsers,
})

const settingsConfigRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings/config',
  component: SettingsConfig,
})

import Login from './pages/Login'

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: Login,
})

import Tasks from './pages/Tasks'

const tasksRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/tasks',
  component: Tasks,
})

import Downloads from './pages/Downloads'

const downloadsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/downloads',
  component: Downloads,
})

import SettingsSearches from './pages/SettingsSearches'

const settingsSearchesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings/searches',
  component: SettingsSearches,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  libraryRoute,
  discoveryRoute,
  settingsSearchesRoute,
  tasksRoute,
  downloadsRoute,
  settingsCategoryRoute,
  settingsUsersRoute,
  settingsConfigRoute,
  loginRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
