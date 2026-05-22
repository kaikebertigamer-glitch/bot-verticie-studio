import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { Bot, Megaphone, BarChart3, ArrowRight, Workflow, Target } from 'lucide-react'

const services = [
  {
    icon: Bot,
    tag: 'Atendimento 24/7',
    title: 'AutomaÃ§Ã£o de Atendimento com IA',
    description:
      'Implantamos agentes de IA treinados no seu negÃ³cio que respondem leads, qualificam clientes e agendam reuniÃµes em menos de 2 minutos â€” no WhatsApp, Instagram e no seu site.',
    bullets: [
      'Chatbot com IA generativa (GPT/Claude)',
      'IntegraÃ§Ã£o nativa com WhatsApp Business',
      'QualificaÃ§Ã£o e roteamento automÃ¡tico',
      'RelatÃ³rios de conversaÃ§Ã£o e conversÃ£o',
    ],
    highlight: 'Mais popular',
    color: 'from-gold-500/10 to-gold-400/5',
    border: 'border-gold-400/20',
    iconBg: 'bg-gold-500/10 border-gold-500/20',
    iconColor: 'text-gold-400',
  },
  {
    icon: Megaphone,
    tag: 'PersuasÃ£o que converte',
    title: 'Marketing de Resposta Direta',
    description:
      'Criamos funis de vendas, e-mail marketing e campanhas de conteÃºdo estratÃ©gico que geram demanda previsÃ­vel â€” sem depender de sorte ou de viralizar.',
    bullets: [
      'Copywriting orientado Ã  conversÃ£o',
      'Funis de captura e nutriÃ§Ã£o de leads',
      'E-mail e SMS marketing automatizados',
      'EstratÃ©gia de conteÃºdo para redes sociais',
    ],
    highlight: null,
    color: 'from-blue-500/8 to-blue-400/3',
    border: 'border-blue-400/15',
    iconBg: 'bg-blue-500/10 border-blue-500/20',
    iconColor: 'text-blue-400',
  },
  {
    icon: BarChart3,
    tag: 'ROI Garantido',
    title: 'GestÃ£o de TrÃ¡fego Pago',
    description:
      'Gerenciamos suas campanhas no Meta Ads e Google Ads com dados e IA para que cada real investido trabalhe pelo mÃ¡ximo retorno possÃ­vel.',
    bullets: [
      'Campanhas no Meta Ads e Google Ads',
      'OtimizaÃ§Ã£o com machine learning',
      'Pixel, rastreamento e atribuiÃ§Ã£o avanÃ§ada',
      'RelatÃ³rios semanais de performance e ROI',
    ],
    highlight: null,
    color: 'from-purple-500/8 to-purple-400/3',
    border: 'border-purple-400/15',
    iconBg: 'bg-purple-500/10 border-purple-500/20',
    iconColor: 'text-purple-400',
  },
  {
    icon: Workflow,
    tag: 'Processos automÃ¡ticos',
    title: 'CRM e Funis de Vendas',
    description:
      'Estruturamos seu CRM, automatizamos o follow-up e criamos pipelines visuais que transformam contatos em clientes sem esforÃ§o manual.',
    bullets: [
      'ConfiguraÃ§Ã£o de CRM (HubSpot / Kommo)',
      'AutomaÃ§Ã£o de follow-up multicanal',
      'Pipeline personalizado para seu nicho',
      'IntegraÃ§Ã£o com WhatsApp e e-mail',
    ],
    highlight: null,
    color: 'from-emerald-500/8 to-emerald-400/3',
    border: 'border-emerald-400/15',
    iconBg: 'bg-emerald-500/10 border-emerald-500/20',
    iconColor: 'text-emerald-400',
  },
  {
    icon: Target,
    tag: 'VisÃ£o estratÃ©gica',
    title: 'Consultoria em EstratÃ©gia Digital',
    description:
      'Mapeamos toda sua operaÃ§Ã£o digital, identificamos onde vocÃª perde dinheiro e entregamos um plano de aÃ§Ã£o com prioridades claras e metas mensurÃ¡veis.',
    bullets: [
      'DiagnÃ³stico 360Â° da operaÃ§Ã£o digital',
      'Plano de aÃ§Ã£o com ROI projetado',
      'PriorizaÃ§Ã£o de iniciativas de maior impacto',
      'Acompanhamento mensal de resultados',
    ],
    highlight: null,
    color: 'from-orange-500/8 to-orange-400/3',
    border: 'border-orange-400/15',
    iconBg: 'bg-orange-500/10 border-orange-500/20',
    iconColor: 'text-orange-400',
  },
]

export default function ServicesSection() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section id="servicos" className="py-24 relative" ref={ref}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gold-500/4 rounded-full blur-[120px]" />
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
            Tudo que sua empresa precisa para{' '}
            <span className="gradient-text">escalar com IA</span>
          </h2>
          <p className="section-subtitle mx-auto text-center">
            SoluÃ§Ãµes integradas e customizadas para o seu negÃ³cio, implementadas por especialistas com visÃ£o de resultado.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((s, i) => {
            const Icon = s.icon
            return (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 30 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.1 + 0.2, duration: 0.6 }}
                className={`relative glass-card p-7 group hover:-translate-y-1 transition-all duration-300 ${s.border} overflow-hidden`}
              >
                {/* Gradient background */}
                <div className={`absolute inset-0 bg-gradient-to-br ${s.color} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                {/* Highlight badge */}
                {s.highlight && (
                  <div className="absolute top-4 right-4 bg-gold-500/20 border border-gold-400/30 text-gold-300 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full">
                    {s.highlight}
                  </div>
                )}

                <div className="relative z-10 space-y-5">
                  <div className="flex items-start gap-4">
                    <div className={`w-11 h-11 rounded-xl border flex items-center justify-center flex-shrink-0 ${s.iconBg}`}>
                      <Icon size={20} className={s.iconColor} />
                    </div>
                    <div>
                      <p className="text-silver-500 text-xs uppercase tracking-widest font-medium mb-1">{s.tag}</p>
                      <h3 className="font-display font-bold text-silver-100 text-lg leading-tight">{s.title}</h3>
                    </div>
                  </div>

                  <p className="text-silver-400 text-sm leading-relaxed">{s.description}</p>

                  <ul className="space-y-2.5">
                    {s.bullets.map((b) => (
                      <li key={b} className="flex items-center gap-2 text-silver-400 text-sm">
                        <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${s.iconColor.replace('text-', 'bg-')}`} />
                        {b}
                      </li>
                    ))}
                  </ul>

                  <a
                    href="https://wa.me/5512991564645?text=OlÃ¡!%20Tenho%20interesse%20no%20serviÃ§o%20de%20automaÃ§Ã£o%20da%20VÃ©rtice%20Studio"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-silver-300 group-hover:text-gold-300 transition-colors duration-200"
                  >
                    Quero esse serviÃ§o
                    <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
                  </a>
                </div>
              </motion.div>
            )
          })}

          {/* CTA card â€” 6th position fills the grid */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.7, duration: 0.6 }}
            className="glass-card p-7 border-gold-400/20 bg-gradient-to-br from-gold-500/10 to-gold-400/5 flex flex-col justify-between relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-400/60 to-transparent" />
            <div className="space-y-4">
              <p className="text-gold-300 text-xs uppercase tracking-widest font-bold">Pronto para comeÃ§ar?</p>
              <h3 className="font-display font-bold text-silver-100 text-2xl leading-tight">
                EstratÃ©gia personalizada para o seu negÃ³cio
              </h3>
              <p className="text-silver-400 text-sm leading-relaxed">
                NÃ£o existe fÃ³rmula genÃ©rica. Agende um diagnÃ³stico gratuito e descubra o melhor caminho para escalar.
              </p>
            </div>
            <a
              href="https://wa.me/5512991564645?text=OlÃ¡!%20Quero%20um%20diagnÃ³stico%20gratuito%20da%20VÃ©rtice%20Studio"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary mt-6 justify-center"
            >
              Agendar DiagnÃ³stico
              <ArrowRight size={16} />
            </a>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

