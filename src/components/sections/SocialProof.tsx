import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { Star, TrendingUp, Users, MessageSquare } from 'lucide-react'

const testimonials = [
  {
    name: 'Rodrigo Mendes',
    role: 'ProprietÃ¡rio â€” ClÃ­nica EstÃ©tica Renovar',
    avatar: 'RM',
    color: 'from-purple-500 to-purple-700',
    stars: 5,
    text: 'Em 30 dias, nossa agenda estava 100% cheia com pacientes qualificados. O chatbot responde dÃºvidas, explica nossos procedimentos e jÃ¡ agenda direto no sistema â€” tudo sozinho. Economizamos 3h por dia sÃ³ no atendimento.',
    metric: '+280% agendamentos',
  },
  {
    name: 'Fernanda Costa',
    role: 'CEO â€” ImobiliÃ¡ria Costa & Filhos',
    avatar: 'FC',
    color: 'from-gold-500 to-gold-700',
    stars: 5,
    text: 'TÃ­nhamos um problema sÃ©rio: leads sumiam porque nÃ£o respondÃ­amos rÃ¡pido. Com a automaÃ§Ã£o da VÃ©rtice, todo lead recebe contato em menos de 1 minuto. Nosso fechamento de contratos aumentou 40% no primeiro trimestre.',
    metric: '+40% fechamentos',
  },
  {
    name: 'Marcos Albuquerque',
    role: 'Diretor â€” Escola de Idiomas Fluent',
    avatar: 'MA',
    color: 'from-blue-500 to-blue-700',
    stars: 5,
    text: 'Investimos em trÃ¡fego pago hÃ¡ anos sem retorno consistente. A VÃ©rtice nÃ£o sÃ³ ajustou nossas campanhas, como criou um funil que converte o trÃ¡fego em matrÃ­culas de forma previsÃ­vel. ROAS de 8x nos Ãºltimos dois meses.',
    metric: 'ROAS 8x',
  },
  {
    name: 'PatrÃ­cia Souza',
    role: 'Fundadora â€” Pet Shop Natural Pets',
    avatar: 'PS',
    color: 'from-emerald-500 to-emerald-700',
    stars: 5,
    text: 'O que mais me impressionou foi a velocidade. Em menos de 2 semanas jÃ¡ tÃ­nhamos o sistema rodando e os primeiros resultados aparecendo. Hoje nosso WhatsApp vende 24h por dia sem que eu precise estar online.',
    metric: 'Vendas 24/7 automatizadas',
  },
  {
    name: 'Carlos Eduardo',
    role: 'SÃ³cio â€” EscritÃ³rio Advocacia Digital',
    avatar: 'CE',
    color: 'from-silver-400 to-silver-600',
    stars: 5,
    text: 'Captamos leads de alto valor e precisÃ¡vamos de follow-up consistente. A VÃ©rtice implementou uma sequÃªncia de automaÃ§Ã£o tÃ£o natural que clientes nÃ£o percebem que Ã© automÃ¡tico â€” e nossos contratos aumentaram 60%.',
    metric: '+60% em contratos',
  },
  {
    name: 'Ana Paula Ribeiro',
    role: 'Diretora â€” Academia FitLife',
    avatar: 'AR',
    color: 'from-orange-500 to-orange-700',
    stars: 5,
    text: 'DiminuÃ­mos nossa taxa de cancelamento em 35% com automaÃ§Ãµes de retenÃ§Ã£o. Mensagens personalizadas no momento certo, avisos de renovaÃ§Ã£o, conteÃºdo de valor â€” tudo automÃ¡tico. O ROI foi imediato.',
    metric: '-35% cancelamentos',
  },
]

export default function SocialProof() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section id="resultados" className="py-24 relative overflow-hidden" ref={ref}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-64 bg-gold-500/4 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16 space-y-4"
        >
          <div className="gold-line mx-auto" />
          <h2 className="section-title">
            Empresas que{' '}
            <span className="gradient-text">transformaram seus resultados</span>
          </h2>
          <p className="section-subtitle mx-auto text-center">
            NÃ£o acredite sÃ³ em nÃ³s. Veja o que nossos clientes conquistaram com automaÃ§Ã£o inteligente.
          </p>

          {/* Trust bar */}
          <div className="flex flex-wrap items-center justify-center gap-8 pt-4">
            <div className="flex items-center gap-2 text-silver-400 text-sm">
              <Star size={15} className="text-gold-400 fill-gold-400" />
              <span><strong className="text-silver-200">4.9/5</strong> â€” avaliaÃ§Ã£o mÃ©dia</span>
            </div>
            <div className="flex items-center gap-2 text-silver-400 text-sm">
              <Users size={15} className="text-gold-400" />
              <span><strong className="text-silver-200">120+</strong> clientes atendidos</span>
            </div>
            <div className="flex items-center gap-2 text-silver-400 text-sm">
              <TrendingUp size={15} className="text-gold-400" />
              <span><strong className="text-silver-200">340%</strong> crescimento mÃ©dio em leads</span>
            </div>
            <div className="flex items-center gap-2 text-silver-400 text-sm">
              <MessageSquare size={15} className="text-gold-400" />
              <span><strong className="text-silver-200">1M+</strong> mensagens automatizadas</span>
            </div>
          </div>
        </motion.div>

        {/* Testimonials grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.1 + 0.2, duration: 0.6 }}
              className="glass-card p-7 flex flex-col gap-5 hover:-translate-y-1 transition-transform duration-300"
            >
              {/* Stars */}
              <div className="flex gap-1">
                {Array.from({ length: t.stars }).map((_, s) => (
                  <Star key={s} size={14} className="text-gold-400 fill-gold-400" />
                ))}
              </div>

              {/* Text */}
              <p className="text-silver-300 text-sm leading-relaxed flex-1">"{t.text}"</p>

              {/* Metric badge */}
              <div className="bg-gold-500/10 border border-gold-400/20 text-gold-300 text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-lg self-start">
                {t.metric}
              </div>

              {/* Author */}
              <div className="flex items-center gap-3 pt-2 border-t border-silver-400/10">
                <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${t.color} flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}>
                  {t.avatar}
                </div>
                <div>
                  <p className="text-silver-200 text-sm font-semibold leading-tight">{t.name}</p>
                  <p className="text-silver-500 text-xs leading-tight">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

