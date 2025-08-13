import { useEffect, useMemo, useState } from 'react'

// Tipos y constantes de estados
 type StatusId = 'trabajando' | 'descanso' | 'almuerzo' | 'bano' | 'capacitacion' | 'soporte'

 const STATUS_LABELS: Record<StatusId, string> = {
   trabajando: 'Trabajando',
   descanso: 'Descanso',
   almuerzo: 'Almuerzo',
   bano: 'Baño',
   capacitacion: 'Capacitación',
   soporte: 'Soporte Técnico',
 }

 function formatTime(totalSeconds: number): string {
   const hours = Math.floor(totalSeconds / 3600)
   const minutes = Math.floor((totalSeconds % 3600) / 60)
   const seconds = totalSeconds % 60
   const hh = String(hours).padStart(2, '0')
   const mm = String(minutes).padStart(2, '0')
   const ss = String(seconds).padStart(2, '0')
   return `${hh}:${mm}:${ss}`
 }

 export default function App() {
   const [now, setNow] = useState<Date>(new Date())
   const [shiftActive, setShiftActive] = useState<boolean>(true)
   const [currentStatus, setCurrentStatus] = useState<StatusId>('trabajando')
   const [secondsByStatus, setSecondsByStatus] = useState<Record<StatusId, number>>({
     trabajando: 0,
     descanso: 0,
     almuerzo: 0,
     bano: 0,
     capacitacion: 0,
     soporte: 0,
   })

   useEffect(() => {
     if (!shiftActive) return

     const intervalId = setInterval(() => {
       setNow(new Date())
       setSecondsByStatus(prev => ({
         ...prev,
         [currentStatus]: prev[currentStatus] + 1,
       }))
     }, 1000)

     return () => clearInterval(intervalId)
   }, [currentStatus, shiftActive])

   const totalWorkedSeconds = useMemo(() => {
     return Object.values(secondsByStatus).reduce((sum, s) => sum + s, 0)
   }, [secondsByStatus])

   const statusButtons: StatusId[] = [
     'trabajando',
     'descanso',
     'almuerzo',
     'bano',
     'capacitacion',
     'soporte',
   ]

   return (
     <div className="min-h-screen bg-gray-100 text-gray-900">
       {/* Header */}
       <header className="w-full border-b bg-white">
         <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
           <div className="flex items-center gap-3">
             <div className="h-9 w-9 rounded-full bg-purple-600 text-white grid place-items-center font-semibold">A</div>
             <div>
               <div className="text-sm font-semibold">Franklin Felipe Pavi Cordoba</div>
               <div className="text-xs text-gray-500">Servicio Al Cliente</div>
             </div>
           </div>
           <button
             className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
             onClick={() => alert('Sesión cerrada (demo)')}
           >
             Cerrar Sesión
           </button>
         </div>
       </header>

       {/* Contenido principal */}
       <main className="max-w-6xl mx-auto px-4 py-6">
         <div className="bg-white rounded-lg shadow-sm border">
           <div className="px-6 py-5 border-b">
             <h1 className="text-2xl font-extrabold text-center">Mi Gestión</h1>
           </div>

           {/* Cards de resumen */}
           <section className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
             <div className="rounded-md border bg-white p-4 shadow-sm">
               <div className="text-sm text-gray-600">Hora Actual</div>
               <div className="mt-1 text-2xl font-bold tabular-nums">
                 {now.toLocaleTimeString('es-EC', { hour12: false })}
               </div>
             </div>
             <div className="rounded-md border bg-white p-4 shadow-sm">
               <div className="text-sm text-gray-600">Tiempo Trabajado</div>
               <div className="mt-1 text-2xl font-bold tabular-nums">
                 {formatTime(totalWorkedSeconds)}
               </div>
             </div>
             <div className="rounded-md border bg-white p-4 shadow-sm">
               <div className="text-sm text-gray-600">Estado Actual</div>
               <div className="mt-1 text-2xl font-bold">{STATUS_LABELS[currentStatus]}</div>
             </div>
           </section>

           {/* Turno */}
           <div className="px-6">
             <div className="w-full rounded-md bg-gray-400 text-white text-center py-3 font-medium">
               {shiftActive ? 'Turno Iniciado' : 'Turno Finalizado'}
             </div>
           </div>

           {/* Estados */}
           <section className="p-6">
             <div className="text-base font-semibold mb-3">Estados</div>
             <div className={`grid grid-cols-1 md:grid-cols-2 gap-3 ${!shiftActive ? 'opacity-60 pointer-events-none' : ''}`}>
               {statusButtons.map((id) => (
                 <button
                   key={id}
                   className={`w-full flex items-center justify-between rounded-md px-4 py-3 text-white shadow-sm transition-colors
                   ${currentStatus === id ? 'bg-blue-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                   onClick={() => setCurrentStatus(id)}
                 >
                   <span className="font-medium">{STATUS_LABELS[id]}</span>
                   <span className="font-semibold tabular-nums">{formatTime(secondsByStatus[id])}</span>
                 </button>
               ))}
             </div>

             <div className="mt-6">
               <button
                 className="w-full rounded-md bg-red-600 hover:bg-red-700 text-white py-3 font-semibold shadow-sm"
                 onClick={() => setShiftActive(false)}
               >
                 Finalizar Turno
               </button>
             </div>
           </section>
         </div>

         {/* Footer */}
         <footer className="text-center text-sm text-gray-500 mt-6">
           © 2025 Desarrollado por JGSolutionsTI
         </footer>
       </main>
     </div>
   )
 }
