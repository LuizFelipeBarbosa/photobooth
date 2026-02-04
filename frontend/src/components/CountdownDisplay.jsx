import { motion, AnimatePresence } from 'framer-motion'

export default function CountdownDisplay({ value, visible }) {
  return (
    <AnimatePresence mode="wait">
      {visible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.5, filter: 'blur(20px)' }}
          animate={{ 
            opacity: 1, 
            scale: 1, 
            filter: 'blur(0px)',
          }}
          exit={{ 
            opacity: 0, 
            scale: 1.5, 
            filter: 'blur(10px)',
          }}
          transition={{ 
            duration: 0.4, 
            ease: [0.175, 0.885, 0.32, 1.275]
          }}
          className="relative flex items-center justify-center"
        >
          {/* Outer glow rings */}
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div 
              className="absolute w-48 h-48 md:w-64 md:h-64 rounded-full border-2 border-[var(--color-accent-primary)]/20"
              animate={{ 
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.1, 0.3],
              }}
              transition={{ 
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
            />
            <motion.div 
              className="absolute w-40 h-40 md:w-56 md:h-56 rounded-full border border-[var(--color-accent-primary)]/30"
              animate={{ 
                scale: [1.1, 0.9, 1.1],
                opacity: [0.2, 0.4, 0.2],
              }}
              transition={{ 
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 0.3
              }}
            />
          </div>

          {/* Background glow */}
          <div className="absolute w-32 h-32 md:w-48 md:h-48 rounded-full bg-[var(--color-accent-primary)] opacity-20 blur-3xl" />

          {/* Countdown number or icon */}
          <motion.div
            key={value}
            initial={{ scale: 0.5, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.5, opacity: 0, y: -20 }}
            transition={{ 
              type: 'spring',
              stiffness: 300,
              damping: 20
            }}
            className="relative z-10"
          >
            {typeof value === 'number' ? (
              <span 
                className="text-8xl md:text-9xl font-black text-gradient animate-countdown"
                style={{ fontFamily: 'Playfair Display, serif' }}
              >
                {value}
              </span>
            ) : (
              <motion.span 
                className="text-7xl md:text-8xl"
                animate={{ 
                  scale: [1, 1.2, 1],
                  rotate: [0, -10, 10, 0],
                }}
                transition={{ 
                  duration: 0.5,
                  ease: 'easeInOut'
                }}
              >
                {value}
              </motion.span>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
