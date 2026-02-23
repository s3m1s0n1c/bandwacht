interface StatusBadgeProps {
  active: boolean
  activeText?: string
  inactiveText?: string
}

export default function StatusBadge({ active, activeText = 'Aktiv', inactiveText = 'Inaktiv' }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
      active
        ? 'bg-sdr-green/10 text-sdr-green'
        : 'bg-sdr-border text-sdr-muted'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-sdr-green' : 'bg-sdr-muted'}`} />
      {active ? activeText : inactiveText}
    </span>
  )
}
