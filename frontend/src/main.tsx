import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import React from 'react'
import ReactDOM from 'react-dom/client'
import './i18n' // Import i18n configuration
import './index.css'
import { router } from './router'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <React.Suspense
        fallback={
          <div className="flex h-screen w-full items-center justify-center bg-zinc-950 text-zinc-400">
            Loading...
          </div>
        }
      >
        <RouterProvider router={router} />
      </React.Suspense>
    </QueryClientProvider>
  </React.StrictMode>,
)
