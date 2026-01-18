import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { AxiosError } from 'axios'
import { Card } from 'components/ui/Card'
import { Input } from 'components/ui/Input'
import { Button } from 'components/ui/Button'
import { login, verifyTfa } from 'api'
import { Lock, User, KeyRound } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function Login() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [tfaCode, setTfaCode] = useState('')
    const [step, setStep] = useState<'login' | 'tfa'>('login')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const res = await login(username, password)
            if (res.tfa_required) {
                setStep('tfa')
            } else if (res.access_token) {
                localStorage.setItem('token', res.access_token)
                await navigate({ to: '/' })
            }
        } catch (err) {
            const error = err as AxiosError<{ detail: string }>
            setError(error.response?.data.detail || t('auth.login_failed'))
        } finally {
            setLoading(false)
        }
    }

    const handleTfa = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const res = await verifyTfa(username, tfaCode)
            if (res.access_token) {
                localStorage.setItem('token', res.access_token)
                await navigate({ to: '/' })
            }
        } catch (err) {
            const error = err as AxiosError<{ detail: string }>
            setError(error.response?.data.detail || t('auth.invalid_code'))
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex items-center justify-center p-4 content-center h-[calc(100vh-100px)]">
            <Card className="max-w-md w-full p-8 border-zinc-800 bg-zinc-900/50">
                <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold text-white mb-2">
                        {step === 'login' ? t('auth.welcome') : t('auth.tfa_title')}
                    </h1>
                    <p className="text-zinc-400">
                        {step === 'login'
                            ? t('auth.signin_desc')
                            : t('auth.tfa_desc')}
                    </p>
                </div>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-md p-3 mb-6">
                        <p className="text-red-400 text-sm text-center">{error}</p>
                    </div>
                )}

                {step === 'login' ? (
                    <form onSubmit={(e) => void handleLogin(e)} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs font-medium text-zinc-500 uppercase">{t('auth.username')}</label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-zinc-500" />
                                <Input
                                    value={username}
                                    onChange={e => { setUsername(e.target.value); }}
                                    className="pl-9 bg-zinc-950/50"
                                    placeholder={t('auth.username_placeholder')}
                                    required
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-medium text-zinc-500 uppercase">{t('auth.password')}</label>
                            <div className="relative">
                                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-zinc-500" />
                                <Input
                                    type="password"
                                    value={password}
                                    onChange={e => { setPassword(e.target.value); }}
                                    className="pl-9 bg-zinc-950/50"
                                    placeholder={t('auth.password_placeholder')}
                                    required
                                />
                            </div>
                        </div>
                        <Button
                            type="submit"
                            className="w-full bg-violet-600 hover:bg-violet-500 text-white"
                            disabled={loading}
                        >
                            {loading ? t('auth.signing_in') : t('auth.signin')}
                        </Button>
                    </form>
                ) : (
                    <form onSubmit={(e) => void handleTfa(e)} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs font-medium text-zinc-500 uppercase">{t('auth.tfa_code')}</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-zinc-500" />
                                <Input
                                    value={tfaCode}
                                    onChange={e => { setTfaCode(e.target.value); }}
                                    className="pl-9 bg-zinc-950/50"
                                    placeholder={t('auth.tfa_placeholder')}
                                    maxLength={6}
                                    required
                                />
                            </div>
                        </div>
                        <Button
                            type="submit"
                            className="w-full bg-violet-600 hover:bg-violet-500 text-white"
                            disabled={loading}
                        >
                            {loading ? t('auth.verifying') : t('auth.verify')}
                        </Button>
                        <Button
                            type="button"
                            variant="ghost"
                            className="w-full text-zinc-500 hover:text-zinc-300"
                            onClick={() => {
                                setStep('login')
                                setTfaCode('')
                                setError('')
                            }}
                        >
                            {t('auth.back_to_login')}
                        </Button>
                    </form>
                )}
            </Card>
        </div>
    )
}
