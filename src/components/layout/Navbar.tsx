import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X } from 'lucide-react'

const links = [
  { label: 'ServiÃ§os', href: '#servicos' },
  { label: 'Por que a VÃ©rtice?', href: '#porque-vertice' },
  { label: 'Resultados', href: '#resultados' },
  { label: 'FAQ', href: '#faq' },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-navy-900/90 backdrop-blur-xl border-b border-silver-400/10 shadow-xl shadow-navy-950/50'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <a href="#" className="flex items-center gap-3 group">
            <div className="w-9 h-9 relative">
              <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
                <polygon points="20,4 36,32 27,32 20,18 13,32 4,32" fill="url(#goldGrad)" />
                <polygon points="20,10 31,30 24,30 20,22 16,30 9,30" fill="#d4dce6" opacity="0.9" />
                <defs>
                  <linearGradient id="goldGrad" x1="4" y1="4" x2="36" y2="32" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#e8c97a" />
                    <stop offset="1" stopColor="#c09642" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div className="leading-none">
              <span className="font-display font-bold text-lg text-silver-100 tracking-wider group-hover:text-gold-300 transition-colors">VÃ‰RTICE</span>
              <span className="block text-xs font-medium text-silver-400 tracking-[0.2em] uppercase">Studio</span>
            </div>
          </a>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-8">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-silver-400 hover:text-silver-100 text-sm font-medium transition-colors duration-200 relative group"
              >
                {l.label}
                <span className="absolute -bottom-0.5 left-0 w-0 h-px bg-gold-400 group-hover:w-full transition-all duration-300" />
              </a>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <a
              href="https://wa.me/5512991564645?text=OlÃ¡!%20Quero%20saber%20mais%20sobre%20os%20serviÃ§os%20da%20VÃ©rtice%20Studio"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-sm py-2.5 px-5"
            >
              Falar com Especialista
            </a>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setOpen(!open)}
            className="md:hidden p-2 text-silver-300 hover:text-gold-300 transition-colors"
            aria-label="Menu"
          >
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden bg-navy-900/95 backdrop-blur-xl border-t border-silver-400/10"
          >
            <div className="px-4 py-6 space-y-4">
              {links.map((l) => (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={() => setOpen(false)}
                  className="block text-silver-300 hover:text-gold-300 font-medium py-2 transition-colors"
                >
                  {l.label}
                </a>
              ))}
              <a
                href="https://wa.me/5512991564645?text=OlÃ¡!%20Quero%20saber%20mais%20sobre%20os%20serviÃ§os%20da%20VÃ©rtice%20Studio"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary w-full justify-center mt-4"
              >
                Falar com Especialista
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  )
}

