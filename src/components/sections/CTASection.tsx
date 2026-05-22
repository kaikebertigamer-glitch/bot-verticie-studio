import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { ArrowRight, MessageCircle, Clock, Shield } from 'lucide-react'

export default function CTASection() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section className="py-24 relative overflow-hidden" ref={ref}>
      {/* Glowing background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-navy-900/50 to-navy-950" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-gold-500/8 rounded-full blur-[100px]" />
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-gold-400/30 to-transparent" />
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="glass-card p-10 md:p-14 text-center border-gold-400/15 relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-400/60 to-transparent" />

          {/* Urgency tag */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={inView ? { opacity: 1, scale: 1 } : {}}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 bg-gold-500/10 border border-gold-500/20 rounded-full px-4 py-1.5 mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
            <span className="text-gold-300 text-xs font-semibold tracking-widest uppercase">Vagas limitadas â€” apenas 5 diagnÃ³sticos gratuitos por semana</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="font-display font-bold text-3xl md:text-5xl text-silver-100 leading-tight mb-6"
          >
            Seu concorrente jÃ¡ estÃ¡
            <br />
            <span className="gradient-text">automatizando.</span>
            <br />
            E vocÃª?
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="text-silver-400 text-lg leading-relaxed mb-10 max-w-2xl mx-auto"
          >
            Cada dia sem automaÃ§Ã£o Ã© mais uma oportunidade perdida para um concorrente que responde mais rÃ¡pido, atende melhor e converte mais. Agende agora um diagnÃ³stico gratuito e descubra quanto vocÃª pode ganhar.
          </motion.p>

          {/* Guarantees */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={inView ? { opacity: 1 } : {}}
            transition={{ delay: 0.5 }}
            className="flex flex-wrap items-center justify-center gap-6 mb-10 text-silver-400 text-sm"
          >
            <div className="flex items-center gap-2">
              <Shield size={15} className="text-gold-400" />
              <span>100% gratuito, sem compromisso</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock size={15} className="text-gold-400" />
              <span>Resposta em atÃ© 2h</span>
            </div>
            <div className="flex items-center gap-2">
              <MessageCircle size={15} className="text-gold-400" />
              <span>Online ou presencial</span>
            </div>
          </motion.div>

          {/* CTA buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <a
              href="https://wa.me/5512991564645?text=OlÃ¡!%20Quero%20agendar%20meu%20diagnÃ³stico%20gratuito%20com%20a%20VÃ©rtice%20Studio"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-base py-4 px-8 animate-pulse-gold"
            >
              <MessageCircle size={18} />
              Agendar DiagnÃ³stico Gratuito
              <ArrowRight size={18} />
            </a>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={inView ? { opacity: 1 } : {}}
            transition={{ delay: 0.8 }}
            className="text-silver-500 text-xs mt-6"
          >
            Sem cartÃ£o de crÃ©dito. Sem letra miÃºda. Apenas um diagnÃ³stico honesto do que pode ser melhorado.
          </motion.p>
        </motion.div>
      </div>
    </section>
  )
}

