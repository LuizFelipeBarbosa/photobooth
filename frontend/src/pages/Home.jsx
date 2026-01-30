import { Link } from 'react-router-dom'
import Header from '../components/Header'
import StatusIndicator from '../components/StatusIndicator'
import CountdownDisplay from '../components/CountdownDisplay'
import PhotoModal from '../components/PhotoModal'
import usePhotobooth from '../hooks/usePhotobooth'

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
    <div className="min-h-screen flex flex-col items-center justify-center p-8 gap-8">
      <Header />

      <StatusIndicator status={status} icon={statusIcon} message={statusMessage} />

      <CountdownDisplay value={countdownValue} visible={showCountdown} />

      <div className="flex flex-col gap-6 w-full max-w-xs">
        <button
          onClick={takePhoto}
          disabled={isCapturing}
          className="flex flex-col items-center justify-center p-8 border-none rounded-3xl cursor-pointer transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 bg-gradient-to-br from-[#e94560] to-[#ff6b6b] shadow-[0_10px_40px_rgba(233,69,96,0.4)] hover:shadow-[0_15px_50px_rgba(233,69,96,0.5)] hover:-translate-y-0.5"
        >
          <span className="text-5xl mb-2">📸</span>
          <span className="text-xl font-semibold text-white">Single Photo</span>
        </button>

        <button
          onClick={takeStrip}
          disabled={isCapturing}
          className="flex flex-col items-center justify-center p-8 border-none rounded-3xl cursor-pointer transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 bg-gradient-to-br from-[#0f3460] to-[#1a5276] shadow-[0_10px_40px_rgba(15,52,96,0.6)] hover:shadow-[0_15px_50px_rgba(15,52,96,0.7)] hover:-translate-y-0.5"
        >
          <span className="text-5xl mb-2">🎞️</span>
          <span className="text-xl font-semibold text-white">Photo Strip</span>
          <span className="text-sm text-white/70 mt-1">3 Photos</span>
        </button>
      </div>

      <Link
        to="/gallery"
        className="mt-4 w-full max-w-xs p-4 rounded-3xl bg-white/10 text-white text-center text-lg font-semibold no-underline hover:bg-white/20 transition-colors"
      >
        📂 View Gallery
      </Link>

      <div className="text-center text-white/70 text-sm">
        <p>📍 Look at the computer camera!</p>
        <p>Photos will print automatically</p>
      </div>

      {/* Flash overlay */}
      <div className={`flash-overlay ${showFlash ? 'active' : ''}`} />

      {/* Result modal */}
      <PhotoModal
        isOpen={!!resultPhoto}
        onClose={closeResult}
        photoUrl={resultPhoto}
        title="Great Shot! 🎉"
        message="Printing your photo..."
      />
    </div>
  )
}
