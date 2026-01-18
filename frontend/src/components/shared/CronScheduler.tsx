import { useState } from 'react'
import { Button } from 'components/ui/Button'
import { Select } from 'components/ui/Select'
import { Input } from 'components/ui/Input'

interface CronSchedulerProps {
    name?: string
    value?: string
    onChange?: (value: string) => void
}

export const CronScheduler = ({ name = 'cron', value = '0 12 * * *', onChange }: CronSchedulerProps) => {
    // Mode preference: 'scheduled' (UI form) or 'raw' (text input)
    // We defer to 'raw' if the current value cannot be represented as simple schedule
    const [preferredMode, setPreferredMode] = useState<'scheduled' | 'raw'>('scheduled')

    // Parse cron to UI state
    const parseCron = (cron: string) => {
        try {
            const parts = cron.split(' ')
            if (parts.length !== 5) return { t: '12:00', f: 'raw' }

            const [m, h, dom, mon, dow] = parts
            const t = `${h.padStart(2, '0')}:${m.padStart(2, '0')}`

            // Heuristic detection of frequency
            let f = 'raw'

            if (dom === '*' && mon === '*' && dow === '*') f = '1_day'
            else if (dom.startsWith('*/') && mon === '*' && dow === '*') f = `${dom.substring(2)}_days`
            else if (dom === '*' && mon === '*' && dow === '1') f = '1_week' // Weekly on Monday
            else if (dom === '1' && mon === '*' && dow === '*') f = '1_month'
            else if (dom === '1' && mon.startsWith('*/') && dow === '*') f = `${mon.substring(2)}_months`
            else if (dom === '1' && mon === '1' && dow === '*') f = '1_year'

            return { t, f }
        } catch {
            return { t: '12:00', f: 'raw' }
        }
    }

    const { t: time, f: calculatedFreq } = parseCron(value)

    // Effective mode: if parsed as raw, force raw. Otherwise use preference.
    const mode = calculatedFreq === 'raw' ? 'raw' : preferredMode

    // Use calculated frequency if valid, otherwise default to 1_day for UI (though effectively hidden in raw mode)
    const frequency = calculatedFreq === 'raw' ? '1_day' : calculatedFreq

    // Generate cron from UI state
    const generateCron = (freq: string, t: string) => {
        const [h, m] = t.split(':')
        const mm = parseInt(m, 10)
        const hh = parseInt(h, 10)

        switch (freq) {
            case '1_day': return `${String(mm)} ${String(hh)} * * *`
            case '2_days': return `${String(mm)} ${String(hh)} */2 * *`
            case '3_days': return `${String(mm)} ${String(hh)} */3 * *`
            case '4_days': return `${String(mm)} ${String(hh)} */4 * *`
            case '5_days': return `${String(mm)} ${String(hh)} */5 * *`
            case '6_days': return `${String(mm)} ${String(hh)} */6 * *`
            case '7_days': return `${String(mm)} ${String(hh)} */7 * *`
            case '1_week': return `${String(mm)} ${String(hh)} * * 1`
            case '2_weeks': return `${String(mm)} ${String(hh)} */14 * *`
            case '3_weeks': return `${String(mm)} ${String(hh)} */21 * *`
            case '4_weeks': return `${String(mm)} ${String(hh)} */28 * *`
            case '1_month': return `${String(mm)} ${String(hh)} 1 * *`
            case '2_months': return `${String(mm)} ${String(hh)} 1 */2 *`
            case '3_months': return `${String(mm)} ${String(hh)} 1 */3 *`
            case '6_months': return `${String(mm)} ${String(hh)} 1 */6 *`
            case '1_year': return `${String(mm)} ${String(hh)} 1 1 *`
            default: return value
        }
    }

    const handleUIChange = (newFreq: string, newTime: string) => {
        const newCron = generateCron(newFreq, newTime)
        onChange?.(newCron)
    }

    const handleRawChange = (val: string) => {
        onChange?.(val)
    }

    const freqOptions = [
        { value: '1_day', label: 'Every Day' },
        { value: '2_days', label: 'Every 2 Days' },
        { value: '3_days', label: 'Every 3 Days' },
        { value: '4_days', label: 'Every 4 Days' },
        { value: '5_days', label: 'Every 5 Days' },
        { value: '6_days', label: 'Every 6 Days' },
        { value: '1_week', label: 'Every Week' },
        { value: '2_weeks', label: 'Every 2 Weeks' },
        { value: '3_weeks', label: 'Every 3 Weeks' },
        { value: '4_weeks', label: 'Every 4 Weeks' },
        { value: '1_month', label: 'Every Month' },
        { value: '2_months', label: 'Every 2 Months' },
        { value: '3_months', label: 'Every 3 Months' },
        { value: '6_months', label: 'Every 6 Months' },
        { value: '1_year', label: 'Every Year' },
    ]

    return (
        <div className="space-y-3">
            <input type="hidden" name={name} value={value} />

            <div className="flex bg-black/50 p-1 rounded-lg border border-zinc-800">
                <Button
                    type="button"
                    variant={mode === 'scheduled' ? 'secondary' : 'ghost'}
                    size="sm"
                    className="flex-1 rounded-md"
                    onClick={() => {
                        setPreferredMode('scheduled')
                        if (calculatedFreq === 'raw') {
                            // Reset to default day/time if switching from complex raw
                            handleUIChange('1_day', '12:00')
                        }
                    }}
                >
                    Scheduled
                </Button>
                <Button
                    type="button"
                    variant={mode === 'raw' ? 'secondary' : 'ghost'}
                    size="sm"
                    className="flex-1 rounded-md"
                    onClick={() => { setPreferredMode('raw'); }}
                >
                    Custom (Cron)
                </Button>
            </div>

            {mode === 'scheduled' && (
                <div className="animate-in fade-in slide-in-from-top-2 duration-200 grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                        <label className="text-[10px] uppercase text-zinc-500 font-bold ml-1">Frequency</label>
                        <Select
                            value={frequency}
                            onChange={(val) => { handleUIChange(String(val), time); }}
                            options={freqOptions}
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[10px] uppercase text-zinc-500 font-bold ml-1">At Time</label>
                        <Input
                            type="time"
                            value={time}
                            onChange={(e) => { handleUIChange(frequency, e.target.value); }}
                            className="text-zinc-200"
                        />
                    </div>
                </div>
            )}

            {mode === 'raw' && (
                <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => { handleRawChange(e.target.value); }}
                        placeholder="* * * * *"
                        className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm font-mono focus:border-violet-500 focus:ring-1 focus:ring-violet-500 outline-none transition-colors"
                    />
                    <div className="text-[10px] text-zinc-600 mt-1 pl-1">
                        Format: min hour dom mon dow
                    </div>
                </div>
            )}
        </div>
    )
}
