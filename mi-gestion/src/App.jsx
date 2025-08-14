import { useEffect, useMemo, useState } from 'react'

const STATES = [
  { key: 'trabajando', label: 'Trabajando' },
  { key: 'descanso', label: 'Descanso' },
  { key: 'almuerzo', label: 'Almuerzo' },
  { key: 'bano', label: 'Baño' },
  { key: 'capacitacion', label: 'Capacitación' },
  { key: 'soporte', label: 'Soporte Técnico' },
]

function pad2(n) {
  return String(n).padStart(2, '0')
}

function formatHMS(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${pad2(h)}:${pad2(m)}:${pad2(s)}`
}

export default function App() {
  const [shiftStartedAt] = useState(() => Date.now())
  const [currentStateKey, setCurrentStateKey] = useState('trabajando')
  const [currentStateStartedAt, setCurrentStateStartedAt] = useState(() => Date.now())
  const [durations, setDurations] = useState(() => {
    const initial = {}
    for (const st of STATES) initial[st.key] = 0
    return initial
  })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const now = useMemo(() => Date.now(), [tick])

  const tiempoTrabajado = Math.floor((now - shiftStartedAt) / 1000)

  function getStateElapsedSeconds(key) {
    const base = durations[key] || 0
    if (currentStateKey === key) {
      return base + Math.floor((now - currentStateStartedAt) / 1000)
    }
    return base
  }

  function switchState(nextKey) {
    if (nextKey === currentStateKey) return
    const elapsed = Math.floor((Date.now() - currentStateStartedAt) / 1000)
    setDurations((prev) => ({
      ...prev,
      [currentStateKey]: (prev[currentStateKey] || 0) + elapsed,
    }))
    setCurrentStateKey(nextKey)
    setCurrentStateStartedAt(Date.now())
  }

  const horaActual = new Date(now).toLocaleTimeString('es-ES', { hour12: false })
  const estadoActualLabel = STATES.find((s) => s.key === currentStateKey)?.label ?? ''

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Top bar */}
      <div className="w-full bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-semibold">
              A
            </div>
            <div>
              <div className="text-gray-900 font-medium">Franklin Felipe Pavi Cordoba</div>
              <div className="text-gray-500 text-sm">Servicio Al Cliente</div>
            </div>
          </div>
          <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium">
            Cerrar Sesión
          </button>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-semibold text-center text-gray-900">Mi Gestión</h2>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="border rounded-lg bg-gray-50 px-4 py-3 text-center">
              <div className="text-sm text-gray-500">Hora Actual</div>
              <div className="text-2xl font-bold text-gray-900 tracking-wider">{horaActual}</div>
            </div>
            <div className="border rounded-lg bg-gray-50 px-4 py-3 text-center">
              <div className="text-sm text-gray-500">Tiempo Trabajado</div>
              <div className="text-2xl font-bold text-gray-900">{formatHMS(tiempoTrabajado)}</div>
            </div>
            <div className="border rounded-lg bg-gray-50 px-4 py-3 text-center">
              <div className="text-sm text-gray-500">Estado Actual</div>
              <div className="text-2xl font-bold text-gray-900">{estadoActualLabel}</div>
            </div>
          </div>

          {/* Banner */}
          <div className="mt-6">
            <div className="w-full bg-gray-400 text-white text-center py-2 rounded-md font-medium">
              Turno Iniciado
            </div>
          </div>

          {/* Estados */}
          <div className="mt-6">
            <div className="text-gray-900 font-medium mb-3">Estados</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {STATES.map((st) => {
                const time = formatHMS(getStateElapsedSeconds(st.key))
                const isActive = currentStateKey === st.key
                return (
                  <button
                    key={st.key}
                    onClick={() => switchState(st.key)}
                    className={`flex items-center justify-between w-full rounded-lg px-4 py-3 font-medium text-white transition-colors ${
                      isActive ? 'bg-blue-700' : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    <span>{st.label}</span>
                    <span className="opacity-95">{time}</span>
                  </button>
                )
              })}
            </div>

            <button className="mt-6 w-full bg-red-600 hover:bg-red-700 text-white rounded-lg py-3 font-medium">
              Finalizar Turno
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 text-center text-gray-500 text-sm">
        © 2025 Desarrollado por JGSolutionsTI
      </footer>
    </div>
  )
}
