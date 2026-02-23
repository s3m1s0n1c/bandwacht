import { X, Volume2 } from 'lucide-react'

interface AudioPlayerProps {
  url: string | null
  onClose: () => void
}

export default function AudioPlayer({ url, onClose }: AudioPlayerProps) {
  if (!url) return null

  const filename = url.split('/').pop() ?? 'recording.wav'

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-sdr-surface border-t border-sdr-border p-3 z-40">
      <div className="max-w-4xl mx-auto flex items-center gap-4">
        <Volume2 className="w-4 h-4 text-sdr-cyan shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-sdr-muted truncate mb-1">{filename}</p>
          <audio controls autoPlay src={url} className="w-full h-8" style={{ colorScheme: 'dark' }} />
        </div>
        <button onClick={onClose} className="text-sdr-muted hover:text-sdr-text shrink-0">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
