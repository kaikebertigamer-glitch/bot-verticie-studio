import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import HeroSection from './components/sections/HeroSection'
import ProblemSolution from './components/sections/ProblemSolution'
import ServicesSection from './components/sections/ServicesSection'
import WhyVertice from './components/sections/WhyVertice'
import SocialProof from './components/sections/SocialProof'
import FAQSection from './components/sections/FAQSection'
import CTASection from './components/sections/CTASection'
import FloatingCTA from './components/ui/FloatingCTA'

function App() {
  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <Navbar />
      <main>
        <HeroSection />
        <ProblemSolution />
        <ServicesSection />
        <WhyVertice />
        <SocialProof />
        <FAQSection />
        <CTASection />
      </main>
      <Footer />
      <FloatingCTA />
    </div>
  )
}

export default App

