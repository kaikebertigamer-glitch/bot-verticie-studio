import { Instagram, MessageCircle, Mail, MapPin } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-navy-950 border-t border-silver-400/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8">
          {/* Brand */}
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9">
                <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
                  <polygon points="20,4 36,32 27,32 20,18 13,32 4,32" fill="url(#goldGrad2)" />
                  <polygon points="20,10 31,30 24,30 20,22 16,30 9,30" fill="#d4dce6" opacity="0.9" />
                  <defs>
                    <linearGradient id="goldGrad2" x1="4" y1="4" x2="36" y2="32" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#e8c97a" />
                      <stop offset="1" stopColor="#c09642" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div>
                <span className="font-display font-bold text-silver-100 tracking-wider">VÃ‰RTICE</span>
                <span className="block text-xs text-silver-400 tracking-[0.2em] uppercase">Studio</span>
              </div>
            </div>
            <p className="text-silver-400 text-sm leading-relaxed max-w-xs">
              Transformamos negÃ³cios regionais com automaÃ§Ã£o inteligente, IA aplicada e estratÃ©gia digital de alto impacto.
            </p>
            <div className="flex items-center gap-4">
              <a
                href="https://instagram.com/vertice_studio2.0"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 flex items-center justify-center rounded-lg bg-navy-800 border border-silver-400/10 text-silver-400 hover:text-gold-300 hover:border-gold-400/30 transition-all duration-200"
                aria-label="Instagram"
              >
                <Instagram size={16} />
              </a>
              <a
                href="https://wa.me/5512991564645"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 flex items-center justify-center rounded-lg bg-navy-800 border border-silver-400/10 text-silver-400 hover:text-gold-300 hover:border-gold-400/30 transition-all duration-200"
                aria-label="WhatsApp"
              >
                <MessageCircle size={16} />
              </a>
            </div>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-display font-semibold text-silver-200 mb-5 text-sm uppercase tracking-widest">ServiÃ§os</h3>
            <ul className="space-y-3">
              {[
                'AutomaÃ§Ã£o de Atendimento com IA',
                'Marketing de Resposta Direta',
                'GestÃ£o de TrÃ¡fego Pago',
                'CRM e Funis de Vendas',
                'Consultoria EstratÃ©gica',
              ].map((s) => (
                <li key={s}>
                  <a href="#servicos" className="text-silver-400 hover:text-gold-300 text-sm transition-colors duration-200">
                    {s}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="font-display font-semibold text-silver-200 mb-5 text-sm uppercase tracking-widest">Contato</h3>
            <ul className="space-y-4">
              <li className="flex items-start gap-3 text-silver-400 text-sm">
                <MessageCircle size={15} className="text-gold-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="block text-silver-300 font-medium">WhatsApp</span>
                  <a href="https://wa.me/5512991564645" className="hover:text-gold-300 transition-colors">+55 (00) 00000-0000</a>
                </div>
              </li>
              <li className="flex items-start gap-3 text-silver-400 text-sm">
                <Mail size={15} className="text-gold-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="block text-silver-300 font-medium">E-mail</span>
                  <a href="mailto:contato@verticestudio.com.br" className="hover:text-gold-300 transition-colors">contato@verticestudio.com.br</a>
                </div>
              </li>
              <li className="flex items-start gap-3 text-silver-400 text-sm">
                <MapPin size={15} className="text-gold-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="block text-silver-300 font-medium">RegiÃ£o de AtuaÃ§Ã£o</span>
                  <span>Brasil â€” Atendimento 100% remoto</span>
                </div>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-silver-400/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-silver-500 text-xs">
            Â© {new Date().getFullYear()} VÃ©rtice Studio. Todos os direitos reservados.
          </p>
          <div className="flex items-center gap-1">
            <div className="h-px w-8 bg-gradient-to-r from-transparent to-gold-500/50" />
            <div className="w-1.5 h-1.5 rounded-full bg-gold-500/70" />
            <div className="h-px w-8 bg-gradient-to-l from-transparent to-gold-500/50" />
          </div>
          <p className="text-silver-500 text-xs">Feito com estratÃ©gia. Entregue com resultado.</p>
        </div>
      </div>
    </footer>
  )
}

