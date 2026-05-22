import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { XCircle, CheckCircle2, ArrowRight } from 'lucide-react'

const problems = [
  'Responde leads horas (ou dias) depois e perde para o concorrente',
  'Gasta tempo em tarefas repetitivas que poderiam ser automatizadas',
  'NÃ£o sabe quais campanhas de marketing realmente funcionam',
  'Equipe sobrecarregada com atendimento manual de baixa qualidade',
  'Processo de vendas inconsistente â€” depende 100% de vocÃª ou de um vendedor',
  'Investe em trÃ¡fego mas nÃ£o converte porque nÃ£o tem funil estruturado',
]

const solutions = [
  'IA responde em menos de 2 minutos, 24/7 â€” inclusive fora do horÃ¡rio comercial',
  'Fluxos automatizados que qualificam, nutrem e agendam sem intervenÃ§Ã£o humana',
  'Dashboards em tempo real com ROI de cada canal de aquisiÃ§Ã£o',
  'Chatbots treinados no seu produto que atendem com precisÃ£o e personalidade',
  'Funil de vendas replicÃ¡vel, previsÃ­vel e escalÃ¡vel â€” com ou sem vocÃª',
  'TrÃ¡fego pago gerenciado com IA para maximizar conversÃ£o e reduzir custo por lead',
]

export default function ProblemSolution() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section id="problema" className="py-24 relative" ref={ref}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-72 h-72 bg-red-500/3 rounded-full blur-[80px]" />
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-72 h-72 bg-gold-500/5 rounded-full blur-[80px]" />
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
            Sua empresa estÃ¡{' '}
            <span className="gradient-text">sangrando receita</span>
            <br />e vocÃª provavelmente nem percebe
          </h2>
          <p className="section-subtitle mx-auto text-center">
            Enquanto vocÃª faz tudo manualmente, concorrentes com automaÃ§Ã£o inteligente estÃ£o capturando seus clientes.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Problems */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="glass-card p-8 border-red-500/10"
          >
            <div className="flex items-center gap-3 mb-7">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <XCircle size={20} className="text-red-400" />
              </div>
              <div>
                <h3 className="font-display font-bold text-silver-100 text-lg">A Realidade Hoje</h3>
                <p className="text-red-400/80 text-xs font-medium uppercase tracking-wider">Sem automaÃ§Ã£o</p>
              </div>
            </div>
            <ul className="space-y-4">
              {problems.map((p, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -15 }}
                  animate={inView ? { opacity: 1, x: 0 } : {}}
                  transition={{ delay: 0.3 + i * 0.08 }}
                  className="flex items-start gap-3 text-silver-400 text-sm leading-relaxed"
                >
                  <XCircle size={16} className="text-red-400/70 mt-0.5 flex-shrink-0" />
                  {p}
                </motion.li>
              ))}
            </ul>
          </motion.div>

          {/* Solutions */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="glass-card p-8 border-gold-500/10 relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-400/40 to-transparent" />
            <div className="flex items-center gap-3 mb-7">
              <div className="w-10 h-10 rounded-xl bg-gold-500/10 border border-gold-500/20 flex items-center justify-center">
                <CheckCircle2 size={20} className="text-gold-400" />
              </div>
              <div>
                <h3 className="font-display font-bold text-silver-100 text-lg">Com a VÃ©rtice Studio</h3>
                <p className="text-gold-400/80 text-xs font-medium uppercase tracking-wider">AutomaÃ§Ã£o inteligente</p>
              </div>
            </div>
            <ul className="space-y-4">
              {solutions.map((s, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: 15 }}
                  animate={inView ? { opacity: 1, x: 0 } : {}}
                  transition={{ delay: 0.4 + i * 0.08 }}
                  className="flex items-start gap-3 text-silver-300 text-sm leading-relaxed"
                >
                  <CheckCircle2 size={16} className="text-gold-400 mt-0.5 flex-shrink-0" />
                  {s}
                </motion.li>
              ))}
            </ul>
          </motion.div>
        </div>

        {/* CTA bridge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="text-center mt-12"
        >
          <a
            href="https://wa.me/5512991564645?text=OlÃ¡!%20Quero%20um%20diagnÃ³stico%20gratuito%20da%20VÃ©rtice%20Studio"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary inline-flex"
          >
            Quero sair desse cenÃ¡rio agora
            <ArrowRight size={18} />
          </a>
        </motion.div>
      </div>
    </section>
  )
}

