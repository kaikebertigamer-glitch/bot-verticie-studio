import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { Cpu, Clock, BarChart2, Users, Layers, MessageSquareCode } from 'lucide-react'
import AnimatedCounter from '../ui/AnimatedCounter'

const stats = [
  { value: 120, suffix: '+', label: 'AutomaÃ§Ãµes Implementadas' },
  { value: 94, suffix: '%', label: 'Taxa de SatisfaÃ§Ã£o dos Clientes' },
  { value: 2, suffix: 'min', label: 'Tempo MÃ©dio de Resposta' },
  { value: 340, suffix: '%', label: 'Crescimento MÃ©dio em Leads' },
]

const differentials = [
  {
    icon: Cpu,
    title: 'IA de Ãšltima GeraÃ§Ã£o',
    description: 'Utilizamos modelos de linguagem avanÃ§ados (GPT-4, Claude) customizados com o DNA do seu negÃ³cio â€” nÃ£o Ã© robÃ´ genÃ©rico.',
  },
  {
    icon: Clock,
    title: 'ImplementaÃ§Ã£o em 15 dias',
    description: 'Do diagnÃ³stico ao sistema funcionando em atÃ© 15 dias Ãºteis. Enquanto outros ainda estÃ£o planejando, vocÃª jÃ¡ estÃ¡ convertendo.',
  },
  {
    icon: BarChart2,
    title: 'Foco em ROI Real',
    description: 'Cada projeto tem mÃ©tricas claras de sucesso. Se nÃ£o gerar resultado mensurÃ¡vel, algo estÃ¡ errado â€” e nÃ³s corrigimos.',
  },
  {
    icon: Users,
    title: 'Especialistas em Regional',
    description: 'Entendemos o comportamento do consumidor regional e construÃ­mos estratÃ©gias que funcionam na sua realidade, nÃ£o em SÃ£o Paulo.',
  },
  {
    icon: Layers,
    title: 'Stack TecnolÃ³gico Premium',
    description: 'Make, n8n, HubSpot, Kommo, Meta Ads API â€” ferramentas profissionais que grandes empresas usam, acessÃ­veis para o seu negÃ³cio.',
  },
  {
    icon: MessageSquareCode,
    title: 'Suporte EstratÃ©gico ContÃ­nuo',
    description: 'NÃ£o entregamos e sumimos. Acompanhamos sua evoluÃ§Ã£o com relatÃ³rios mensais, otimizaÃ§Ãµes e suporte dedicado.',
  },
]

export default function WhyVertice() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section id="porque-vertice" className="py-24 relative" ref={ref}>
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-gold-400/20 to-transparent" />
        <div className="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-gold-400/20 to-transparent" />
        <div className="absolute top-1/4 -right-40 w-96 h-96 bg-gold-500/5 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16 space-y-4"
        >
          <div className="gold-line mx-auto" />
          <h2 className="section-title">
            Por que a{' '}
            <span className="gradient-text">VÃ©rtice Studio</span>
            ?
          </h2>
          <p className="section-subtitle mx-auto text-center">
            NÃ£o somos mais uma agÃªncia genÃ©rica. Somos especialistas em transformar negÃ³cios reais com tecnologia que funciona.
          </p>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={inView ? { opacity: 1, scale: 1 } : {}}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="glass-card p-6 text-center relative overflow-hidden group hover:border-gold-400/20 transition-colors duration-300"
            >
              <div className="absolute inset-0 bg-gradient-to-b from-gold-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="relative z-10">
                <div className="font-display font-bold text-3xl md:text-4xl text-gold-300 mb-1">
                  {inView ? (
                    <>
                      <AnimatedCounter value={stat.value} />
                      <span>{stat.suffix}</span>
                    </>
                  ) : (
                    <span>0{stat.suffix}</span>
                  )}
                </div>
                <p className="text-silver-400 text-xs md:text-sm leading-tight">{stat.label}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Differentials grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {differentials.map((d, i) => {
            const Icon = d.icon
            return (
              <motion.div
                key={d.title}
                initial={{ opacity: 0, y: 25 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.3 + i * 0.1, duration: 0.6 }}
                className="flex items-start gap-5 group"
              >
                <div className="w-11 h-11 rounded-xl bg-gold-500/10 border border-gold-500/20 flex items-center justify-center flex-shrink-0 group-hover:bg-gold-500/15 group-hover:border-gold-400/30 transition-all duration-300">
                  <Icon size={20} className="text-gold-400" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-display font-semibold text-silver-100 text-base">{d.title}</h3>
                  <p className="text-silver-400 text-sm leading-relaxed">{d.description}</p>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Process timeline */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="mt-20"
        >
          <h3 className="font-display font-bold text-silver-100 text-2xl text-center mb-10">
            Como funciona o processo
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 relative">
            {/* Connection line */}
            <div className="hidden lg:block absolute top-8 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-gold-400/20 via-gold-400/50 to-gold-400/20" />

            {[
              { step: '01', title: 'DiagnÃ³stico', desc: 'Mapeamos sua operaÃ§Ã£o digital em uma reuniÃ£o estratÃ©gica' },
              { step: '02', title: 'EstratÃ©gia', desc: 'Criamos um plano personalizado com prioridades e ROI projetado' },
              { step: '03', title: 'ImplementaÃ§Ã£o', desc: 'Nossa equipe configura tudo em atÃ© 15 dias Ãºteis' },
              { step: '04', title: 'OtimizaÃ§Ã£o', desc: 'Monitoramos resultados e otimizamos continuamente' },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.9 + i * 0.1, duration: 0.5 }}
                className="glass-card p-6 text-center relative"
              >
                <div className="w-12 h-12 rounded-full bg-gold-500/15 border border-gold-400/30 flex items-center justify-center mx-auto mb-4 relative z-10">
                  <span className="font-display font-bold text-gold-300 text-sm">{item.step}</span>
                </div>
                <h4 className="font-display font-semibold text-silver-100 mb-2">{item.title}</h4>
                <p className="text-silver-400 text-sm leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

