import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import PhotoModal from '../components/PhotoModal'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, scale: 0.8, y: 20 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.175, 0.885, 0.32, 1.275],
    },
  },
}

export default function Gallery() {
  const [photos, setPhotos] = useState([])
  const [loading, setLoading] = useState(true)
  const [currentSort, setCurrentSort] = useState('date_desc')
  const [filterLiked, setFilterLiked] = useState(false)
  const [selectedPhoto, setSelectedPhoto] = useState(null)
  const [statusMsg, setStatusMsg] = useState('')
  const [reprinting, setReprinting] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const loadPhotos = useCallback(async () => {
    try {
      const response = await fetch('/api/photos')
      const data = await response.json()
      setPhotos(data.photos || [])
    } catch (e) {
      console.error('Failed to load photos', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPhotos()
  }, [loadPhotos])

  const displayPhotos = (() => {
    let result = [...photos]

    if (filterLiked) {
      result = result.filter((p) => p.liked)
    }

    if (currentSort === 'date_desc') {
      result.sort((a, b) => b.timestamp - a.timestamp)
    } else if (currentSort === 'date_asc') {
      result.sort((a, b) => a.timestamp - b.timestamp)
    }

    return result
  })()

  const formatDate = (timestamp) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const toggleLike = async (filename, e) => {
    if (e) e.stopPropagation()

    const photo = photos.find((p) => p.filename === filename)
    if (!photo) return

    const wasLiked = photo.liked
    // Optimistic update
    setPhotos((prev) =>
      prev.map((p) => (p.filename === filename ? { ...p, liked: !wasLiked } : p))
    )

    if (selectedPhoto?.filename === filename) {
      setSelectedPhoto((prev) => (prev ? { ...prev, liked: !wasLiked } : null))
    }

    try {
      await fetch(`/api/like/${filename}`, { method: 'POST' })
    } catch (e) {
      // Revert on error
      setPhotos((prev) =>
        prev.map((p) => (p.filename === filename ? { ...p, liked: wasLiked } : p))
      )
    }
  }

  const reprintPhoto = async () => {
    if (!selectedPhoto || reprinting) return

    setReprinting(true)
    setStatusMsg('Sending to printer...')

    try {
      const res = await fetch(`/api/reprint/${selectedPhoto.filename}`, {
        method: 'POST',
      })
      const data = await res.json()

      if (data.status === 'success') {
        setStatusMsg('✅ Printing started!')
        setTimeout(() => setSelectedPhoto(null), 2000)
      } else {
        setStatusMsg('❌ Error: ' + data.message)
      }
    } catch (e) {
      setStatusMsg('❌ Connection error')
    } finally {
      setReprinting(false)
    }
  }

  const deletePhoto = async () => {
    if (!selectedPhoto || deleting) return

    if (!confirm('Are you sure you want to delete this photo? This cannot be undone.')) {
      return
    }

    setDeleting(true)
    setStatusMsg('Deleting...')

    try {
      const res = await fetch(`/api/delete/${selectedPhoto.filename}`, {
        method: 'POST',
      })
      const data = await res.json()

      if (data.status === 'success') {
        setStatusMsg('✅ Photo deleted!')
        setPhotos((prev) => prev.filter((p) => p.filename !== selectedPhoto.filename))
        setTimeout(() => setSelectedPhoto(null), 1000)
      } else {
        setStatusMsg('❌ Error: ' + data.message)
      }
    } catch (e) {
      setStatusMsg('❌ Connection error')
    } finally {
      setDeleting(false)
    }
  }

  const openPhoto = (photo) => {
    setSelectedPhoto(photo)
    setStatusMsg('')
  }

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.header 
        className="flex flex-col md:flex-row md:flex-wrap justify-between items-start md:items-center gap-4 mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="group flex items-center gap-2 px-4 py-2.5 rounded-xl glass text-white no-underline hover:bg-white/10 transition-all"
          >
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
              className="group-hover:-translate-x-1 transition-transform"
            >
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </motion.svg>
            <span className="font-medium">Back</span>
          </Link>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold m-0">
              <span className="bg-gradient-to-r from-white to-[var(--color-accent-primary)] bg-clip-text text-transparent">
                Gallery
              </span>
            </h1>
            <p className="text-white/40 text-sm mt-1">{photos.length} photos captured</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <FilterButton
            active={currentSort === 'date_desc'}
            onClick={() => setCurrentSort('date_desc')}
            icon="🕐"
            label="Newest"
          />
          <FilterButton
            active={currentSort === 'date_asc'}
            onClick={() => setCurrentSort('date_asc')}
            icon="📜"
            label="Oldest"
          />
          <FilterButton
            active={filterLiked}
            onClick={() => setFilterLiked(!filterLiked)}
            icon={filterLiked ? '❤️' : '🤍'}
            label="Favorites"
            variant="pink"
          />
        </div>
      </motion.header>

      {/* Photo Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-10 h-10 border-3 border-white/20 border-t-[var(--color-accent-primary)] rounded-full"
          />
        </div>
      ) : displayPhotos.length === 0 ? (
        <motion.div 
          className="text-center py-20"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="text-6xl mb-4">📷</div>
          <p className="text-white/50 text-xl font-medium">
            {filterLiked ? 'No favorites yet.' : 'No photos found.'}
          </p>
          <p className="text-white/30 text-sm mt-2">
            {filterLiked ? 'Like some photos to see them here!' : 'Take your first photo to get started!'}
          </p>
        </motion.div>
      ) : (
        <motion.div 
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <AnimatePresence>
            {displayPhotos.map((photo, index) => (
              <motion.div
                key={photo.filename}
                variants={itemVariants}
                layout
                whileHover={{ scale: 1.03, y: -5 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => openPhoto(photo)}
                className="group relative aspect-square rounded-2xl overflow-hidden cursor-pointer bg-[var(--color-bg-tertiary)] shadow-lg hover:shadow-2xl transition-shadow"
              >
                {/* Photo */}
                <img
                  src={`/photos/${photo.filename}`}
                  alt="Photo"
                  loading="lazy"
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                
                {/* Hover overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300">
                  {/* Date */}
                  <div className="absolute bottom-3 left-3 right-3">
                    <p className="text-white/70 text-xs font-medium">
                      {formatDate(photo.timestamp)}
                    </p>
                  </div>
                  
                  {/* Like button */}
                  <motion.button
                    onClick={(e) => toggleLike(photo.filename, e)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className={`
                      absolute top-3 right-3 w-9 h-9 rounded-full flex items-center justify-center
                      backdrop-blur-md transition-all
                      ${photo.liked 
                        ? 'bg-[var(--color-accent-primary)] text-white shadow-lg' 
                        : 'bg-black/30 text-white/70 hover:bg-white hover:text-[var(--color-accent-primary)]'
                      }
                    `}
                  >
                    {photo.liked ? '❤️' : '🤍'}
                  </motion.button>
                </div>

                {/* Liked indicator (visible when not hovering) */}
                {photo.liked && (
                  <div className="absolute top-3 right-3 w-8 h-8 rounded-full bg-[var(--color-accent-primary)] flex items-center justify-center text-white text-sm shadow-lg group-hover:opacity-0 transition-opacity">
                    ❤️
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Photo Modal */}
      <PhotoModal
        isOpen={!!selectedPhoto}
        onClose={() => setSelectedPhoto(null)}
        photoUrl={selectedPhoto ? `/photos/${selectedPhoto.filename}` : null}
        title={null}
      >
        {/* Photo info */}
        {selectedPhoto && (
          <div className="text-center mb-4">
            <p className="text-white/50 text-sm">
              {formatDate(selectedPhoto.timestamp)}
            </p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-wrap justify-center gap-3">
          <ActionButton
            onClick={() => toggleLike(selectedPhoto?.filename)}
            variant={selectedPhoto?.liked ? 'liked' : 'default'}
            icon={selectedPhoto?.liked ? '❤️' : '🤍'}
            label={selectedPhoto?.liked ? 'Liked' : 'Like'}
          />

          <ActionButton
            onClick={reprintPhoto}
            disabled={reprinting}
            variant="primary"
            icon="🖨️"
            label={reprinting ? 'Printing...' : 'Reprint'}
          />

          <ActionButton
            onClick={deletePhoto}
            disabled={deleting}
            variant="danger"
            icon="🗑️"
            label={deleting ? 'Deleting...' : 'Delete'}
          />
        </div>

        {/* Status message */}
        <AnimatePresence>
          {statusMsg && (
            <motion.p 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-4 text-center text-white/60 text-sm"
            >
              {statusMsg}
            </motion.p>
          )}
        </AnimatePresence>
      </PhotoModal>
    </div>
  )
}

// Filter button component
function FilterButton({ active, onClick, icon, label, variant = 'default' }) {
  const baseClasses = 'flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-200'
  
  const variants = {
    default: active
      ? 'bg-white text-[var(--color-bg-primary)] shadow-lg'
      : 'glass text-white hover:bg-white/10',
    pink: active
      ? 'bg-[var(--color-accent-primary)] text-white shadow-lg shadow-[var(--color-accent-primary)]/30'
      : 'glass text-white hover:bg-white/10',
  }

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${baseClasses} ${variants[variant]}`}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </motion.button>
  )
}

// Action button component
function ActionButton({ onClick, disabled, variant = 'default', icon, label }) {
  const baseClasses = 'flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
  
  const variants = {
    default: 'glass text-white hover:bg-white/10',
    liked: 'bg-[var(--color-accent-primary)]/20 text-[var(--color-accent-primary)] border border-[var(--color-accent-primary)]/50 hover:bg-[var(--color-accent-primary)]/30',
    primary: 'bg-[var(--color-accent-primary)] text-white shadow-lg shadow-[var(--color-accent-primary)]/30 hover:shadow-xl hover:shadow-[var(--color-accent-primary)]/40 hover:-translate-y-0.5',
    danger: 'bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500 hover:text-white hover:border-red-500',
  }

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      className={`${baseClasses} ${variants[variant]}`}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </motion.button>
  )
}
