import { useCallback, useEffect, useState } from 'react'
import { Radio, Target, Sliders, Bell } from 'lucide-react'
import { instances as instancesApi, targets as targetsApi } from '../../api/client'
import { UI } from '../../utils/strings'
import InstanceList from './InstanceList'
import TargetList from './TargetList'
import DetectionSettings from './DetectionSettings'
import NotificationConfig from './NotificationConfig'
import type { SdrInstance, WatchTarget } from '../../types'

export default function ConfigPage() {
  const [instances, setInstances] = useState<SdrInstance[]>([])
  const [allTargets, setAllTargets] = useState<WatchTarget[]>([])

  const refreshInstances = useCallback(async () => {
    const data = await instancesApi.list()
    setInstances(data)
  }, [])

  const refreshTargets = useCallback(async () => {
    const data = await targetsApi.list()
    setAllTargets(data)
  }, [])

  const refreshAll = useCallback(() => {
    refreshInstances()
    refreshTargets()
  }, [refreshInstances, refreshTargets])

  useEffect(() => { refreshAll() }, [refreshAll])

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Radio className="w-4 h-4 text-sdr-cyan" />
          <h3 className="text-sm font-medium">{UI.cfg_instances}</h3>
        </div>
        <InstanceList instances={instances} onRefresh={refreshAll} />
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Target className="w-4 h-4 text-sdr-cyan" />
          <h3 className="text-sm font-medium">{UI.cfg_targets}</h3>
        </div>
        <TargetList targets={allTargets} instances={instances} onRefresh={refreshTargets} />
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Sliders className="w-4 h-4 text-sdr-cyan" />
          <h3 className="text-sm font-medium">{UI.cfg_detection}</h3>
        </div>
        <DetectionSettings />
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="w-4 h-4 text-sdr-cyan" />
          <h3 className="text-sm font-medium">{UI.cfg_notifications}</h3>
        </div>
        <NotificationConfig />
      </div>
    </div>
  )
}
