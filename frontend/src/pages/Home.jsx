import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import Header from '../components/Header'
import StatusIndicator from '../components/StatusIndicator'
import CountdownDisplay from '../components/CountdownDisplay'
import PhotoModal from '../components/PhotoModal'
import usePhotobooth from '../hooks/usePhotobooth'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.175, 0.885, 0.32, 1.275],
    },
  },
}

export default function Home() {
  const {
    status,
    statusIcon,
    statusMessage,
    countdownValue,
    showCountdown,
    showFlash,
    resultPhoto,
    isCapturing,
    takePhoto,
    takeStrip,
    closeResult,
  } = usePhotobooth()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 md:p-8 gap-6 md:gap-8 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-[var(--color-accent-primary)] opacity-5 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-[var(--color-blue-primary)] opacity-5 rounded-full blur-3xl" />
      </div>

      <Header />

      {/* Main content area */}
      <motion.div 
        className="flex flex-col items-center gap-6 w-full max-w-md"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Status indicator */}
        <motion.div variants={itemVariants}>
          <StatusIndicator status={status} icon={statusIcon} message={statusMessage} />
        </motion.div>

        {/* Countdown display */}
        <div className="h-40 flex items-center justify-center">
          <CountdownDisplay value={countdownValue} visible={showCountdown} />
        </div>

        {/* Action buttons */}
        <motion.div 
          className="flex flex-col gap-4 w-full"
          variants={itemVariants}
        >
          {/* Single Photo Button */}
          <motion.button
            onClick={takePhoto}
            disabled={isCapturing}
            whileHover={{ scale: isCapturing ? 1 : 1.02, y: isCapturing ? 0 : -2 }}
            whileTap={{ scale: isCapturing ? 1 : 0.98 }}
            className={`
              group relative flex items-center gap-4 p-6 rounded-2xl
              bg-gradient-to-r from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)]
              shadow-[0_8px_32px_rgba(255,51,102,0.3)]
              transition-all duration-300
              disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
              hover:shadow-[0_12px_48px_rgba(255,51,102,0.4)]
              overflow-hidden
            `}
          >
            {/* Shimmer effect */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            
            {/* Icon */}
            <div className="w-14 h-14 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-3xl shadow-inner">
              📸
            </div>
            
            {/* Text */}
            <div className="flex-1 text-left">
              <span className="block text-xl font-bold text-white">Single Photo</span>
              <span className="text-sm text-white/70">Quick snapshot</span>
            </div>
            
            {/* Arrow */}
            <motion.svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className="text-white/60 group-hover:text-white group-hover:translate-x-1 transition-all"
            >
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </motion.svg>
          </motion.button>

          {/* Photo Strip Button */}
          <motion.button
            onClick={takeStrip}
            disabled={isCapturing}
            whileHover={{ scale: isCapturing ? 1 : 1.02, y: isCapturing ? 0 : -2 }}
            whileTap={{ scale: isCapturing ? 1 : 0.98 }}
            className={`
              group relative flex items-center gap-4 p-6 rounded-2xl
              bg-gradient-to-r from-[var(--color-blue-primary)] to-[var(--color-blue-secondary)]
              shadow-[0_8px_32px_rgba(79,172,254,0.3)]
              transition-all duration-300
              disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
              hover:shadow-[0_12px_48px_rgba(79,172,254,0.4)]
              overflow-hidden
            `}
          >
            {/* Shimmer effect */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            
            {/* Icon */}
            <div className="w-14 h-14 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-3xl shadow-inner">
              🎞️
            </div>
            
            {/* Text */}
            <div className="flex-1 text-left">
              <span className="block text-xl font-bold text-white">Photo Strip</span>
              <span className="text-sm text-white/70">3 poses in a row</span>
            </div>
            
            {/* Arrow */}
            <motion.svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className="text-white/60 group-hover:text-white group-hover:translate-x-1 transition-all"
            >
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </motion.svg>
          </motion.button>
        </motion.div>

        {/* Gallery Link */}
        <motion.div variants={itemVariants} className="w-full">
          <Link
            to="/gallery"
            className="group flex items-center justify-center gap-3 p-4 rounded-2xl glass text-white no-underline hover:bg-white/10 transition-all duration-300"
          >
            <span className="text-xl">📂</span>
            <span className="font-medium">View Gallery</span>
            <motion.svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="18" 
              height="18" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className="opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all"
            >
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </motion.svg>
          </Link>
        </motion.div>

        {/* Info text */}
        <motion.div 
          variants={itemVariants}
          className="text-center space-y-1"
        >
          <p className="text-white/50 text-sm">
            <span className="inline-flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Look at the camera & smile!
            </span>
          </p>
          <p className="text-white/30 text-xs">
            Photos print automatically
          </p>
        </motion.div>
      </motion.div>

      {/* Flash overlay */}
      <div className={`flash-overlay ${showFlash ? 'active' : ''}`} />

      {/* Result modal */}
      <PhotoModal
        isOpen={!!resultPhoto}
        onClose={closeResult}
        photoUrl={resultPhoto}
        title="Perfect Shot! ✨"
        message="Your photo is printing..."
      />
    </div>
  )
}
