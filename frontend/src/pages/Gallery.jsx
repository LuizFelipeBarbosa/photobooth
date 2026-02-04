import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import PhotoModal from '../components/PhotoModal'
import { apiFetch } from '../lib/api'

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
      const response = await apiFetch('/api/photos')
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
      await apiFetch(`/api/like/${filename}`, { method: 'POST' })
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
      const res = await apiFetch(`/api/reprint/${selectedPhoto.filename}`, {
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
      const res = await apiFetch(`/api/delete/${selectedPhoto.filename}`, {
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
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <header className="flex flex-wrap justify-between items-center gap-4 mb-8">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 px-4 py-2 rounded-full border-2 border-white/20 text-white no-underline hover:bg-white/10 hover:border-white transition-all"
          >
            ← Back
          </Link>
          <h1 className="text-3xl font-bold m-0">Gallery</h1>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setCurrentSort('date_desc')}
            className={`flex items-center gap-2 px-4 py-2 rounded-full border text-white transition-all ${
              currentSort === 'date_desc'
                ? 'bg-[#e94560] border-[#e94560]'
                : 'bg-white/10 border-white/20 hover:bg-white/20'
            }`}
          >
            🕐 Newest
          </button>
          <button
            onClick={() => setCurrentSort('date_asc')}
            className={`flex items-center gap-2 px-4 py-2 rounded-full border text-white transition-all ${
              currentSort === 'date_asc'
                ? 'bg-[#e94560] border-[#e94560]'
                : 'bg-white/10 border-white/20 hover:bg-white/20'
            }`}
          >
            📜 Oldest
          </button>
          <button
            onClick={() => setFilterLiked(!filterLiked)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full border text-white transition-all ${
              filterLiked
                ? 'bg-[#e94560] border-[#e94560]'
                : 'bg-white/10 border-white/20 hover:bg-white/20'
            }`}
          >
            {filterLiked ? '❤️' : '🤍'} Favorites
          </button>
        </div>
      </header>

      {/* Photo Grid */}
      {loading ? (
        <p className="text-center text-white/50 text-xl">Loading...</p>
      ) : displayPhotos.length === 0 ? (
        <p className="text-center text-white/50 text-xl">No photos found.</p>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-6">
          {displayPhotos.map((photo) => (
            <div
              key={photo.filename}
              onClick={() => openPhoto(photo)}
              className="relative bg-[#1a1a1a] rounded-2xl overflow-hidden aspect-square cursor-pointer transition-transform hover:scale-[1.02] hover:z-10 shadow-lg hover:shadow-xl group"
            >
              <img
                src={`/photos/${photo.filename}`}
                alt="Photo"
                loading="lazy"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center p-4">
                <button
                  onClick={(e) => toggleLike(photo.filename, e)}
                  className={`w-10 h-10 rounded-full flex items-center justify-center backdrop-blur-md transition-all hover:scale-105 ${
                    photo.liked
                      ? 'bg-white text-[#ff4757]'
                      : 'bg-white/20 text-white hover:bg-white hover:text-[#e94560]'
                  }`}
                >
                  {photo.liked ? '❤️' : '🤍'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Photo Modal */}
      <PhotoModal
        isOpen={!!selectedPhoto}
        onClose={() => setSelectedPhoto(null)}
        photoUrl={selectedPhoto ? `/photos/${selectedPhoto.filename}` : null}
        title={null}
      >
        <div className="flex flex-wrap justify-center gap-3 mt-4">
          <button
            onClick={() => toggleLike(selectedPhoto?.filename)}
            className={`flex items-center gap-2 px-6 py-3 rounded-full border-2 font-semibold transition-all ${
              selectedPhoto?.liked
                ? 'text-[#ff4757] border-[#ff4757] bg-[rgba(255,71,87,0.1)]'
                : 'text-gray-700 border-gray-200 bg-gray-50 hover:bg-gray-100'
            }`}
          >
            {selectedPhoto?.liked ? '❤️' : '🤍'} Like
          </button>

          <button
            onClick={reprintPhoto}
            disabled={reprinting}
            className="flex items-center gap-2 px-6 py-3 rounded-full bg-[#e94560] text-white font-semibold shadow-[0_4px_15px_rgba(233,69,96,0.4)] hover:shadow-[0_6px_20px_rgba(233,69,96,0.6)] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            🖨️ {reprinting ? 'Printing...' : 'Reprint'}
          </button>

          <button
            onClick={deletePhoto}
            disabled={deleting}
            className="flex items-center gap-2 px-6 py-3 rounded-full border border-[rgba(255,71,87,0.3)] bg-[rgba(255,71,87,0.1)] text-[#ff4757] font-semibold hover:bg-[#ff4757] hover:text-white hover:border-[#ff4757] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            🗑️ {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>

        {statusMsg && (
          <p className="mt-4 text-gray-500">{statusMsg}</p>
        )}
      </PhotoModal>
    </div>
  )
}
