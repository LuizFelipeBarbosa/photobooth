import { useEffect } from 'react'

export default function PhotoModal({ isOpen, onClose, photoUrl, title = 'Great Shot! 🎉', message = 'Printing your photo...', children }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-3xl p-6 max-w-lg w-full max-h-[90vh] overflow-auto text-center animate-modal-pop shadow-2xl relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-4 text-3xl text-gray-400 hover:text-gray-800 transition-colors"
        >
          ×
        </button>

        {title && (
          <h2 className="text-2xl font-bold text-gray-800 mb-4">{title}</h2>
        )}

        {photoUrl && (
          <div className="bg-gray-100 p-2 rounded-lg shadow-md mb-4">
            <img
              src={photoUrl}
              alt="Captured Photo"
              className="max-w-full max-h-[50vh] mx-auto rounded"
            />
          </div>
        )}

        {message && !children && (
          <p className="text-gray-500 animate-pulse-scale">{message}</p>
        )}

        {children}
      </div>
    </div>
  )
}
