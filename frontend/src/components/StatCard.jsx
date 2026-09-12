export default function StatCard({ label, value, tone = 'mint', icon }) {
  return (
    <div className={`stat-card ${tone}`}>
      <div className="stat-card-top">
        <span className="stat-label">{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <strong>{value}</strong>
    </div>
  )
}

