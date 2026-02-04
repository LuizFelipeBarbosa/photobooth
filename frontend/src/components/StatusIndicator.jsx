import { motion, AnimatePresence } from 'framer-motion'

const statusConfig = {
  ready: {
    icon: '📷',
    label: 'Ready',
    gradient: 'from-white/10 to-white/5',
    borderColor: 'border-white/20',
    glowColor: 'shadow-none',
    dotColor: 'bg-emerald-400',
  },
  capturing: {
    icon: '⚡',
    label: 'Capturing',
    gradient: 'from-[var(--color-accent-primary)]/20 to-[var(--color-accent-secondary)]/10',
    borderColor: 'border-[var(--color-accent-primary)]/50',
    glowColor: 'shadow-[0_0_30px_rgba(255,51,102,0.3)]',
    dotColor: 'bg-[var(--color-accent-primary)] animate-pulse',
  },
  success: {
    icon: '✨',
    label: 'Success',
    gradient: 'from-emerald-500/20 to-emerald-400/10',
    borderColor: 'border-emerald-400/50',
    glowColor: 'shadow-[0_0_30px_rgba(0,217,163,0.3)]',
    dotColor: 'bg-emerald-400',
  },
  error: {
    icon: '⚠️',
    label: 'Error',
    gradient: 'from-red-500/20 to-red-400/10',
    borderColor: 'border-red-400/50',
    glowColor: 'shadow-[0_0_30px_rgba(255,71,87,0.3)]',
    dotColor: 'bg-red-400',
  },
}

export default function StatusIndicator({ status, icon, message }) {
  const config = statusConfig[status] || statusConfig.ready
  const displayIcon = icon || config.icon

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        initial={{ opacity: 0, y: 10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.3, ease: [0.175, 0.885, 0.32, 1.275] }}
        className={`
          relative flex items-center gap-4 px-6 py-3 rounded-full
          bg-gradient-to-r ${config.gradient}
          border ${config.borderColor}
          backdrop-blur-xl
          ${config.glowColor}
          transition-all duration-500
        `}
      >
        {/* Animated dot indicator */}
        <div className="relative">
          <div className={`w-2.5 h-2.5 rounded-full ${config.dotColor}`} />
          {status === 'capturing' && (
            <>
              <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-[var(--color-accent-primary)] animate-ping" />
              <div className="absolute -inset-2 rounded-full border border-[var(--color-accent-primary)]/30 animate-pulse" />
            </>
          )}
        </div>

        {/* Icon */}
        <motion.span 
          className="text-2xl"
          initial={{ rotate: -10, scale: 0.8 }}
          animate={{ rotate: 0, scale: 1 }}
          transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
        >
          {displayIcon}
        </motion.span>

        {/* Message */}
        <div className="flex flex-col">
          <span className="text-xs font-medium text-white/50 uppercase tracking-wider">
            {config.label}
          </span>
          <span className="text-sm md:text-base font-semibold text-white leading-tight">
            {message}
          </span>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
