import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, X } from 'lucide-react'

export default function FloatingCTA() {
  const [visible, setVisible] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!dismissed) setVisible(true)
    }, 4000)
    const onScroll = () => {
      if (window.scrollY > 300 && !dismissed) setVisible(true)
    }
    window.addEventListener('scroll', onScroll)
    return () => {
      clearTimeout(timer)
      window.removeEventListener('scroll', onScroll)
    }
  }, [dismissed])

  if (dismissed) return null

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Expanded card */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 10 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="glass-card p-5 max-w-[260px] shadow-2xl shadow-navy-950/60 border-gold-400/20"
          >
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-400/50 to-transparent rounded-t-2xl" />
            <button
              onClick={() => setExpanded(false)}
              className="absolute top-3 right-3 text-silver-500 hover:text-silver-300 transition-colors"
              aria-label="Fechar"
            >
              <X size={14} />
            </button>
            <p className="text-gold-300 text-xs font-bold uppercase tracking-widest mb-2">Fale com um especialista</p>
            <p className="text-silver-300 text-sm leading-snug mb-4">
              Descubra como automatizar suas vendas. DiagnÃ³stico gratuito e sem compromisso.
            </p>
            <a
              href="https://wa.me/5512991564645?text=OlÃ¡!%20Quero%20um%20diagnÃ³stico%20gratuito%20da%20VÃ©rtice%20Studio"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-xs py-2.5 px-4 w-full justify-center"
              onClick={() => setExpanded(false)}
            >
              Falar no WhatsApp
            </a>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main FAB */}
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 20 }}
            className="relative"
          >
            {/* Dismiss button */}
            <button
              onClick={() => { setDismissed(true); setVisible(false) }}
              className="absolute -top-1 -left-1 w-5 h-5 rounded-full bg-navy-700 border border-silver-400/20 flex items-center justify-center text-silver-400 hover:text-silver-200 transition-colors z-10"
              aria-label="Fechar"
            >
              <X size={10} />
            </button>

            <button
              onClick={() => setExpanded(!expanded)}
              className="w-14 h-14 rounded-full bg-gold-500 hover:bg-gold-400 shadow-lg shadow-gold-500/40 hover:shadow-gold-400/50 flex items-center justify-center transition-all duration-300 animate-pulse-gold"
              aria-label="Falar no WhatsApp"
            >
              <MessageCircle size={24} className="text-navy-900" />
            </button>

            {/* Notification dot */}
            {!expanded && (
              <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 border-2 border-navy-900 rounded-full animate-pulse" />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

