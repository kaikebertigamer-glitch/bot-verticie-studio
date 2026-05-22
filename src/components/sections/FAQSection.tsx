import { useState, useRef } from 'react'
import { motion, AnimatePresence, useInView } from 'framer-motion'
import { ChevronDown } from 'lucide-react'

const faqs = [
  {
    q: 'Meu negÃ³cio Ã© pequeno. AutomaÃ§Ã£o com IA Ã© para mim?',
    a: 'Especialmente para vocÃª. Pequenos negÃ³cios ganham proporcionalmente muito mais com automaÃ§Ã£o porque nÃ£o tÃªm equipe grande para cobrir todos os processos. Um chatbot com IA pode substituir um atendente full-time e ainda performar melhor â€” respondendo instantaneamente, sem erros e sem faltar ao trabalho.',
  },
  {
    q: 'Quanto tempo leva para ver os primeiros resultados?',
    a: 'A maioria dos nossos clientes comeÃ§a a ver resultados nos primeiros 15 a 30 dias apÃ³s a implementaÃ§Ã£o. Isso inclui leads sendo respondidos mais rÃ¡pido, mais agendamentos e menor perda de oportunidades. MÃ©tricas mais robustas como ROI de trÃ¡fego e aumento de receita ficam mais claras em 60 a 90 dias.',
  },
  {
    q: 'Preciso de conhecimento tÃ©cnico para usar as ferramentas?',
    a: 'Nenhum. Entregamos tudo configurado e funcionando. Nossa equipe cuida de toda a parte tÃ©cnica â€” vocÃª sÃ³ recebe o resultado. Se quiser entender melhor o funcionamento, oferecemos treinamento incluÃ­do no projeto.',
  },
  {
    q: 'As ferramentas que vocÃªs usam tÃªm custo mensal?',
    a: 'Sim, algumas ferramentas como CRM, plataformas de automaÃ§Ã£o e API do WhatsApp tÃªm custo mensal. Esses custos sÃ£o transparentes e apresentados antes da contrataÃ§Ã£o. Na maioria dos casos, o retorno gerado paga esses custos em poucas semanas. Trabalhamos com ferramentas que entregam o mÃ¡ximo de valor pelo custo.',
  },
  {
    q: 'Como Ã© feita a integraÃ§Ã£o com o meu WhatsApp Business?',
    a: 'Utilizamos a API oficial do WhatsApp Business (Meta), que Ã© 100% aprovada e nÃ£o viola os termos de uso. O processo de integraÃ§Ã£o leva entre 24 e 48 horas e nossa equipe faz tudo â€” vocÃª nÃ£o precisa fazer nada alÃ©m de aprovar o acesso ao seu nÃºmero.',
  },
  {
    q: 'VocÃªs oferecem suporte apÃ³s a implementaÃ§Ã£o?',
    a: 'Sim. Todos os projetos incluem um perÃ­odo de suporte de 30 dias apÃ³s o lanÃ§amento para ajustes e otimizaÃ§Ãµes. Oferecemos tambÃ©m planos de manutenÃ§Ã£o mensal que incluem relatÃ³rios de performance, otimizaÃ§Ãµes contÃ­nuas e suporte prioritÃ¡rio.',
  },
  {
    q: 'O chatbot vai parecer robÃ³tico para os meus clientes?',
    a: 'NÃ£o, se for bem treinado â€” e Ã© exatamente isso que fazemos. Nossos agentes de IA sÃ£o treinados com a linguagem, produtos, objeÃ§Ãµes e personalidade da sua empresa. Clientes regularmente nÃ£o percebem que estÃ£o falando com um sistema automatizado, especialmente nos primeiros contatos.',
  },
  {
    q: 'Como funciona o diagnÃ³stico gratuito?',
    a: 'Ã‰ uma reuniÃ£o de 45 a 60 minutos (online ou presencial) onde mapeamos sua operaÃ§Ã£o digital atual, identificamos os maiores gargalos e oportunidades, e apresentamos um plano de aÃ§Ã£o com estimativa de resultado. Sem custo e sem compromisso. Se fizer sentido para ambos os lados, avanÃ§amos. Se nÃ£o, vocÃª fica com insights valiosos de graÃ§a.',
  },
]

function FAQItem({ q, a, index, inView }: { q: string; a: string; index: number; inView: boolean }) {
  const [open, setOpen] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.07 + 0.2, duration: 0.5 }}
      className="border border-silver-400/10 rounded-xl overflow-hidden"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-4 p-6 text-left hover:bg-navy-800/40 transition-colors duration-200 group"
        aria-expanded={open}
      >
        <span className="font-display font-semibold text-silver-200 group-hover:text-silver-100 transition-colors text-sm md:text-base leading-snug">
          {q}
        </span>
        <ChevronDown
          size={18}
          className={`text-gold-400 flex-shrink-0 transition-transform duration-300 ${open ? 'rotate-180' : ''}`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="answer"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <p className="text-silver-400 text-sm leading-relaxed px-6 pb-6">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function FAQSection() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section id="faq" className="py-24 relative" ref={ref}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-silver-400/10 to-transparent" />
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-14 space-y-4"
        >
          <div className="gold-line mx-auto" />
          <h2 className="section-title">
            DÃºvidas que todo mundo tem{' '}
            <span className="gradient-text">antes de decidir</span>
          </h2>
          <p className="section-subtitle mx-auto text-center">
            TransparÃªncia total. Se sua dÃºvida nÃ£o estÃ¡ aqui, Ã© sÃ³ nos perguntar no WhatsApp.
          </p>
        </motion.div>

        <div className="space-y-3">
          {faqs.map((item, i) => (
            <FAQItem key={i} q={item.q} a={item.a} index={i} inView={inView} />
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.9, duration: 0.5 }}
          className="text-center mt-10 space-y-3"
        >
          <p className="text-silver-400 text-sm">Ainda tem alguma dÃºvida?</p>
          <a
            href="https://wa.me/5512991564645?text=OlÃ¡!%20Tenho%20uma%20dÃºvida%20sobre%20os%20serviÃ§os%20da%20VÃ©rtice%20Studio"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline inline-flex"
          >
            Falar com um especialista
          </a>
        </motion.div>
      </div>
    </section>
  )
}

