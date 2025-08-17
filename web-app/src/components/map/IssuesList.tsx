'use client'

import { useEffect, useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { SC1_DESCRIPTIONS, SC4_DESCRIPTIONS } from '@/utils/statusCodes'

export interface NetworkIssue {
  id: string
  type: 'line-pole-mismatch' | 'other'
  severity: 'error' | 'warning' | 'info'
  title: string
  description: string
  elements: {
    conductorId?: string
    fromPoleId?: string
    toPoleId?: string
  }
}

interface IssuesListProps {
  networkData: any
  onClose?: () => void
  onSelectElement?: (type: string, id: string) => void
}

export default function IssuesList({ networkData, onClose, onSelectElement }: IssuesListProps) {
  const [issues, setIssues] = useState<NetworkIssue[]>([])
  const [isMinimized, setIsMinimized] = useState(false)

  useEffect(() => {
    if (!networkData) return

    const detectedIssues: NetworkIssue[] = []
    
    // Create maps for quick lookups
    const poleMap = new Map<string, any>()
    const connectionMap = new Map<string, any>()
    
    networkData.poles?.forEach((pole: any) => {
      poleMap.set(pole.id, pole)
    })
    
    networkData.connections?.forEach((conn: any) => {
      connectionMap.set(conn.id, conn)
    })

    // Check each conductor for line-pole status mismatches
    networkData.conductors?.forEach((conductor: any) => {
      // Only check conductors that are installed (SC4 >= 3)
      if (conductor.st_code_4 >= 3) {
        const fromNode = poleMap.get(conductor.from) || connectionMap.get(conductor.from)
        const toNode = poleMap.get(conductor.to) || connectionMap.get(conductor.to)
        
        const problematicPoles: string[] = []
        
        // Check from node - only check poles, not connections
        if (fromNode && poleMap.has(conductor.from)) {
          if (fromNode.st_code_1 !== 9) {
            problematicPoles.push(`${conductor.from} (SC1=${fromNode.st_code_1 || 0})`)
          }
        }
        
        // Check to node - only check poles, not connections
        if (toNode && poleMap.has(conductor.to)) {
          if (toNode.st_code_1 !== 9) {
            problematicPoles.push(`${conductor.to} (SC1=${toNode.st_code_1 || 0})`)
          }
        }
        
        if (problematicPoles.length > 0) {
          detectedIssues.push({
            id: `issue-${conductor.id}`,
            type: 'line-pole-mismatch',
            severity: 'warning',
            title: `Conductor ${conductor.id} Status Mismatch`,
            description: `Conductor is ${SC4_DESCRIPTIONS[conductor.st_code_4]} (SC4=${conductor.st_code_4}) but connects to pole(s) without conductor attached status: ${problematicPoles.join(', ')}`,
            elements: {
              conductorId: conductor.id,
              fromPoleId: conductor.from,
              toPoleId: conductor.to
            }
          })
        }
      }
    })

    setIssues(detectedIssues)
  }, [networkData])

  if (issues.length === 0) return null

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'text-red-600 bg-red-50'
      case 'warning': return 'text-orange-600 bg-orange-50'
      case 'info': return 'text-blue-600 bg-blue-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className={`fixed bottom-4 right-4 z-[1000] bg-white rounded-lg shadow-lg border border-gray-200 ${isMinimized ? 'w-48' : 'w-96 max-h-96'}`}>
      <div className="flex items-center justify-between p-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-600" />
          <span className="font-semibold text-sm">Network Issues ({issues.length})</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-gray-500 hover:text-gray-700"
          >
            {isMinimized ? '□' : '—'}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
      
      {!isMinimized && (
        <div className="max-h-80 overflow-y-auto">
          {issues.map((issue) => (
            <div
              key={issue.id}
              className={`p-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 cursor-pointer ${getSeverityColor(issue.severity)}`}
              onClick={() => {
                if (onSelectElement && issue.elements.conductorId) {
                  onSelectElement('conductor', issue.elements.conductorId)
                }
              }}
            >
              <div className="font-medium text-sm mb-1">{issue.title}</div>
              <div className="text-xs opacity-90">{issue.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
