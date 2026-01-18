import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router'
import App from './App'
import Home from './pages/Home'
import LibraryPage from './pages/Library'
import SettingsCategory from './pages/SettingsCategory'
import SettingsUsers from './pages/SettingsUsers'
import SettingsConfig from './pages/SettingsConfig'


const rootRoute = createRootRoute({
    component: App,
})

const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: Home,
})

const libraryRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/library',
    component: LibraryPage,
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

const routeTree = rootRoute.addChildren([
    indexRoute,
    libraryRoute,
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
