const statusStyles = {
  ready: 'border-white/20',
  capturing: 'bg-[rgba(233,69,96,0.2)] border-[#e94560] animate-pulse-scale',
  success: 'bg-[rgba(0,210,106,0.2)] border-[#00d26a]',
  error: 'bg-[rgba(255,71,87,0.2)] border-[#ff4757]',
}

export default function StatusIndicator({ status, icon, message }) {
  return (
    <div
      className={`flex items-center gap-4 px-6 py-4 rounded-full bg-white/10 backdrop-blur-md border transition-all duration-300 ${
        statusStyles[status] || statusStyles.ready
      }`}
    >
      <span className="text-2xl">{icon}</span>
      <span className="text-lg font-semibold">{message}</span>
    </div>
  )
}
