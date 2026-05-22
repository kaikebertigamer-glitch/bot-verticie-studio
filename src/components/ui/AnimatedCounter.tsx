import { useEffect, useState } from 'react'

interface Props {
  value: number
  duration?: number
}

export default function AnimatedCounter({ value, duration = 1800 }: Props) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    const start = Date.now()
    const step = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(eased * value))
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [value, duration])

  return <>{count}</>
}

