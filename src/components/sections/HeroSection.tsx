import { motion } from 'framer-motion'
import { ArrowRight, Zap, TrendingUp, Shield } from 'lucide-react'

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.7, ease: [0.22, 1, 0.36, 1] },
  }),
}

const badges = [
  { icon: Zap, label: 'IA Aplicada ao NegÃ³cio' },
  { icon: TrendingUp, label: 'Resultados MensurÃ¡veis' },
  { icon: Shield, label: 'EstratÃ©gia Exclusiva' },
]

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center pt-20 pb-16 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-gold-500/5 rounded-full blur-[120px]" />
        <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-navy-600/30 rounded-full blur-[80px]" />
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(rgba(196,208,219,1) 1px, transparent 1px), linear-gradient(90deg, rgba(196,208,219,1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left â€” copy */}
          <div className="space-y-8">
            {/* Tag */}
            <motion.div
              custom={0}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="inline-flex items-center gap-2 bg-gold-500/10 border border-gold-500/20 rounded-full px-4 py-1.5"
            >
              <span className="w-2 h-2 rounded-full bg-gold-400 animate-pulse" />
              <span className="text-gold-300 text-xs font-semibold tracking-widest uppercase">AutomaÃ§Ã£o com IA para negÃ³cios regionais</span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              custom={1}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] text-silver-100"
            >
              Pare de perder clientes{' '}
              <span className="gradient-text">enquanto dorme.</span>{' '}
              Automatize suas vendas com IA.
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              custom={2}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="text-silver-400 text-lg sm:text-xl leading-relaxed max-w-xl"
            >
              A VÃ©rtice Studio escaneia sua operaÃ§Ã£o, identifica gargalos e implementa sistemas de automaÃ§Ã£o que respondem leads, qualificam clientes e fecham vendas â€” 24h por dia, sem precisar de vocÃª.
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              custom={3}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="flex flex-col sm:flex-row gap-4"
            >
              <a
                href="https://wa.me/5512991564645?text=OlÃ¡!%20Quero%20um%20diagnÃ³stico%20gratuito%20da%20VÃ©rtice%20Studio"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary text-base animate-pulse-gold"
              >
                Quero DiagnÃ³stico Gratuito
                <ArrowRight size={18} />
              </a>
              <a href="#servicos" className="btn-outline text-base">
                Ver ServiÃ§os
              </a>
            </motion.div>

            {/* Trust badges */}
            <motion.div
              custom={4}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="flex flex-wrap gap-4 pt-2"
            >
              {badges.map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-2 text-silver-500 text-sm">
                  <Icon size={14} className="text-gold-400" />
                  <span>{label}</span>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Right â€” visual card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
            className="relative lg:pl-8"
          >
            {/* Main card */}
            <div className="relative glass-card p-8 overflow-hidden">
              {/* Decorative top border */}
              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-400/50 to-transparent" />

              <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-silver-500 text-xs uppercase tracking-widest font-medium">Dashboard de AutomaÃ§Ã£o</p>
                    <h3 className="font-display font-bold text-silver-100 text-lg mt-1">VÃ©rtice Studio â€” IA</h3>
                  </div>
                  <span className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold px-3 py-1 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Ativo
                  </span>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Leads Respondidos', value: '1.847', change: '+23%', color: 'text-emerald-400' },
                    { label: 'Taxa de ConversÃ£o', value: '34,2%', change: '+8,1%', color: 'text-emerald-400' },
                    { label: 'Tempo de Resposta', value: '< 2min', change: '-91%', color: 'text-gold-300' },
                    { label: 'Atendimentos/dia', value: '240+', change: '+320%', color: 'text-emerald-400' },
                  ].map((stat) => (
                    <div key={stat.label} className="bg-navy-900/60 rounded-xl p-4 border border-silver-400/5">
                      <p className="text-silver-500 text-xs mb-1 leading-tight">{stat.label}</p>
                      <p className="font-display font-bold text-silver-100 text-xl">{stat.value}</p>
                      <p className={`text-xs font-medium mt-0.5 ${stat.color}`}>{stat.change} este mÃªs</p>
                    </div>
                  ))}
                </div>

                {/* Activity feed */}
                <div className="space-y-2.5">
                  <p className="text-silver-500 text-xs uppercase tracking-widest font-medium">Atividade Recente</p>
                  {[
                    { action: 'Lead qualificado automaticamente', time: 'agora mesmo', dot: 'bg-emerald-400' },
                    { action: 'Proposta enviada via WhatsApp', time: '3 min atrÃ¡s', dot: 'bg-gold-400' },
                    { action: 'Agendamento confirmado â€” IA', time: '7 min atrÃ¡s', dot: 'bg-blue-400' },
                  ].map((item) => (
                    <div key={item.action} className="flex items-center gap-3 text-sm">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${item.dot}`} />
                      <span className="text-silver-300 flex-1 truncate">{item.action}</span>
                      <span className="text-silver-500 text-xs flex-shrink-0">{item.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Floating mini card */}
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute -bottom-6 -left-6 glass-card p-4 shadow-xl shadow-navy-950/50 max-w-[180px]"
            >
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center flex-shrink-0">
                  <TrendingUp size={14} className="text-gold-400" />
                </div>
                <div>
                  <p className="text-silver-500 text-[10px] leading-none mb-0.5">Receita automatizada</p>
                  <p className="font-display font-bold text-gold-300 text-sm">+R$ 47.800</p>
                  <p className="text-silver-500 text-[10px]">Ãºltimo mÃªs</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="flex justify-center mt-16"
        >
          <a href="#problema" className="flex flex-col items-center gap-2 text-silver-500 hover:text-gold-400 transition-colors group">
            <span className="text-xs uppercase tracking-widest">Descubra o problema</span>
            <motion.div
              animate={{ y: [0, 6, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-5 h-8 border border-silver-400/30 group-hover:border-gold-400/50 rounded-full flex items-start justify-center pt-1.5 transition-colors"
            >
              <div className="w-1 h-1.5 bg-gold-400 rounded-full" />
            </motion.div>
          </a>
        </motion.div>
      </div>
    </section>
  )
}

