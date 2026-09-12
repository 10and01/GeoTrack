export default function SectionHeading({ eyebrow, title, action }) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <div className="section-eyebrow">{eyebrow}</div>}
        <h2>{title}</h2>
      </div>
      {action && <div className="section-heading-right">{action}</div>}
    </div>
  )
}

