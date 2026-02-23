import { AlertTriangle } from 'lucide-react'
import { UI } from '../../utils/strings'

interface ConfirmDialogProps {
  open: boolean
  message: string
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({ open, message, onConfirm, onCancel }: ConfirmDialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="card max-w-sm w-full space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-sdr-red/10 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-sdr-red" />
          </div>
          <p className="text-sm">{message}</p>
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="btn-ghost">{UI.no}</button>
          <button onClick={onConfirm} className="btn-danger">{UI.yes}</button>
        </div>
      </div>
    </div>
  )
}
