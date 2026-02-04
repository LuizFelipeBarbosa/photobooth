import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function PhotoModal({ 
  isOpen, 
  onClose, 
  photoUrl, 
  title = 'Great Shot! 🎉', 
  message = 'Printing your photo...', 
  children 
}) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
      return () => {
        document.removeEventListener('keydown', handleEscape)
        document.body.style.overflow = ''
      }
    }
  }, [isOpen, onClose])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          {/* Background particles/decorations */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <motion.div
              animate={{ 
                y: [0, -20, 0],
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{ duration: 3, repeat: Infinity }}
              className="absolute top-1/4 left-1/4 text-4xl"
            >
              ✨
            </motion.div>
            <motion.div
              animate={{ 
                y: [0, -15, 0],
                opacity: [0.2, 0.5, 0.2],
              }}
              transition={{ duration: 2.5, repeat: Infinity, delay: 0.5 }}
              className="absolute top-1/3 right-1/4 text-3xl"
            >
              📸
            </motion.div>
            <motion.div
              animate={{ 
                y: [0, -25, 0],
                opacity: [0.2, 0.4, 0.2],
              }}
              transition={{ duration: 3.5, repeat: Infinity, delay: 1 }}
              className="absolute bottom-1/3 left-1/3 text-2xl"
            >
              🎉
            </motion.div>
          </div>

          {/* Modal content */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0, y: 50 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 50 }}
            transition={{ 
              type: 'spring',
              stiffness: 300,
              damping: 25
            }}
            className="relative bg-gradient-to-b from-[#2a2a4a] to-[#1a1a2e] rounded-3xl p-6 md:p-8 max-w-lg w-full max-h-[90vh] overflow-auto shadow-2xl border border-white/10"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <motion.button
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              onClick={onClose}
              className="absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-full bg-white/10 text-white/60 hover:text-white hover:bg-white/20 transition-colors z-10"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </motion.button>

            {/* Title */}
            {title && (
              <motion.h2 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="text-2xl md:text-3xl font-bold text-center mb-6"
              >
                <span className="bg-gradient-to-r from-white to-[var(--color-accent-primary)] bg-clip-text text-transparent">
                  {title}
                </span>
              </motion.h2>
            )}

            {/* Photo display */}
            {photoUrl && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                className="relative mb-6"
              >
                {/* Photo frame effect */}
                <div className="relative bg-white p-3 rounded-lg shadow-2xl transform rotate-1 hover:rotate-0 transition-transform duration-300">
                  {/* Tape effect */}
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 w-16 h-6 bg-white/20 backdrop-blur-sm rounded-sm" />
                  
                  <img
                    src={photoUrl}
                    alt="Captured Photo"
                    className="w-full rounded max-h-[50vh] object-contain bg-gray-100"
                  />
                </div>
                
                {/* Shadow */}
                <div className="absolute -bottom-4 left-4 right-4 h-8 bg-black/30 blur-xl rounded-full" />
              </motion.div>
            )}

            {/* Message */}
            {message && !children && (
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-center text-white/60 animate-pulse"
              >
                {message}
              </motion.p>
            )}

            {/* Custom children content */}
            {children && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {children}
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
