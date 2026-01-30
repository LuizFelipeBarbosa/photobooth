export default function CountdownDisplay({ value, visible }) {
  if (!visible) return null

  return (
    <div className="text-8xl font-extrabold text-white drop-shadow-[0_0_40px_#e94560] animate-pulse-scale my-4">
      {value}
    </div>
  )
}
