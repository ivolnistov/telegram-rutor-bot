import { Link, Outlet, useLocation } from '@tanstack/react-router'
import { LayoutDashboard, Library, MonitorPlay, Settings, Clock, Download } from 'lucide-react'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { Toaster } from 'sonner'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from './components/LanguageSwitcher'

const App = () => {
  const { t } = useTranslation()
  const location = useLocation()

  const isLogin = location.pathname === '/login'

  const showHeader = !isLogin

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-violet-500/30">
      {/* Background Gradients */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[10%] left-[10%] size-[500px]  bg-violet-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[10%] right-[10%] size-[500px]  bg-emerald-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto p-6">
        {showHeader && (
          <header className="flex items-center justify-between mb-12 py-6 border-b border-zinc-800/50 backdrop-blur-sm sticky top-0 z-50 bg-zinc-950/80">
            <div className="flex items-center gap-4">
              <div className="size-10  bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-violet-600/20">
                <MonitorPlay className="size-6  text-white" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight">Rutor Bot</h1>
            </div>

            <div className="flex items-center gap-4">
              <nav className="flex items-center gap-2 bg-zinc-900/50 p-1 rounded-lg border border-zinc-800">
                <Link
                  to="/"
                  className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 [&.active]:bg-zinc-800 [&.active]:text-white [&.active]:shadow-sm"
                  activeProps={{ className: 'bg-zinc-800 text-white shadow-sm' }}
                >
                  <LayoutDashboard className="size-4 " />
                  {t('sidebar.dashboard')}
                </Link>
                <Link
                  to="/library"
                  className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 [&.active]:bg-zinc-800 [&.active]:text-white [&.active]:shadow-sm"
                >
                  <Library className="size-4 " />
                  {t('sidebar.torrents')}
                </Link>
                <Link
                  to="/tasks"
                  className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 [&.active]:bg-zinc-800 [&.active]:text-white [&.active]:shadow-sm"
                >
                  <Clock className="size-4 " />
                  {t('sidebar.tasks')}
                </Link>
                <Link
                  to="/downloads"
                  className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 [&.active]:bg-zinc-800 [&.active]:text-white [&.active]:shadow-sm"
                >
                  <Download className="size-4 " />
                  {t('downloads.title', 'Downloads')}
                </Link>
                <Link
                  to="/settings/category"
                  className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 [&.active]:bg-zinc-800 [&.active]:text-white [&.active]:shadow-sm"
                >
                  <Settings className="size-4 " />
                  {t('sidebar.settings')}
                </Link>
              </nav>
              <LanguageSwitcher />
            </div>
          </header>
        )}

        <main className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Outlet />
        </main>
      </div>
      <TanStackRouterDevtools />
      <Toaster theme="dark" position="top-right" richColors />
    </div>
  )
}

export default App
