import { motion } from 'framer-motion'

export default function Header() {
  return (
    <motion.header 
      className="text-center relative"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.175, 0.885, 0.32, 1.275] }}
    >
      {/* Decorative line above */}
      <motion.div 
        className="flex items-center justify-center gap-3 mb-4"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <div className="h-px w-12 bg-gradient-to-r from-transparent to-white/30" />
        <div className="w-2 h-2 rounded-full bg-[var(--color-accent-primary)] animate-pulse-glow" />
        <div className="h-px w-12 bg-gradient-to-l from-transparent to-white/30" />
      </motion.div>

      {/* Main title */}
      <div className="relative inline-block">
        <motion.h1 
          className="font-display text-5xl md:text-7xl font-black tracking-tight"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, duration: 0.6, ease: [0.175, 0.885, 0.32, 1.275] }}
        >
          <span className="bg-gradient-to-br from-white via-white to-[var(--color-accent-primary)] bg-clip-text text-transparent">
            THE OCHO
          </span>
        </motion.h1>
        
        {/* Glow effect behind title */}
        <div className="absolute inset-0 blur-3xl bg-[var(--color-accent-primary)] opacity-20 -z-10 scale-75" />
      </div>

      {/* Subtitle */}
      <motion.p 
        className="text-sm md:text-base font-medium tracking-[0.4em] text-white/60 mt-3 uppercase"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.5 }}
      >
        Photobooth
      </motion.p>

      {/* Decorative elements */}
      <motion.div 
        className="flex items-center justify-center gap-2 mt-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.5 }}
      >
        <span className="text-xl">📷</span>
        <span className="text-white/30">✦</span>
        <span className="text-xl">🎞️</span>
      </motion.div>
    </motion.header>
  )
}
