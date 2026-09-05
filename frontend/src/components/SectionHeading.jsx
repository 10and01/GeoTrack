export default function SectionHeading({ eyebrow, title, meta, action }) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <div className="section-eyebrow">{eyebrow}</div>}
        <h2>{title}</h2>
      </div>
      <div className="section-heading-right">{meta && <span>{meta}</span>}{action}</div>
    </div>
  )
}

