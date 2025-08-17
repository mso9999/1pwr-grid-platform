'use client'

import { useState, useEffect } from 'react'
import { X, Save, Edit2, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatStatusCode, SC1_COLORS, SC3_COLORS, SC4_COLORS, SC5_COLORS } from '@/utils/statusCodes'

export interface ElementDetail {
  type: 'pole' | 'connection' | 'conductor' | 'transformer' | 'generation'
  id: string
  name?: string
  data: any
}

interface ElementDetailPanelProps {
  element: ElementDetail | null
  onClose: () => void
  onUpdate?: (id: string, updates: any) => Promise<boolean>
  onEdit?: (element: any) => void
  existingNames?: Set<string>
}

export function ElementDetailPanel({ 
  element, 
  onClose, 
  onUpdate,
  onEdit,
  existingNames = new Set()
}: ElementDetailPanelProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedName, setEditedName] = useState('')
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (element) {
      setEditedName(element.name || element.id)
      setIsEditing(false)
      setError('')
    }
  }, [element])

  if (!element) return null

  const handleSave = async () => {
    // Validate uniqueness
    if (editedName !== element.id && existingNames.has(editedName)) {
      setError('This name already exists. Names must be unique.')
      return
    }

    if (!editedName.trim()) {
      setError('Name cannot be empty.')
      return
    }

    setIsSaving(true)
    try {
      if (onUpdate) {
        const success = await onUpdate(element.id, { name: editedName })
        if (success) {
          setIsEditing(false)
          setError('')
        } else {
          setError('Failed to update element.')
        }
      }
    } catch (err) {
      setError('An error occurred while saving.')
    } finally {
      setIsSaving(false)
    }
  }

  const getStatusColor = () => {
    switch (element.type) {
      case 'pole':
        return SC1_COLORS[element.data.st_code_1] || '#808080'
      case 'connection':
        return SC3_COLORS[element.data.st_code_3] || '#808080'
      case 'conductor':
        return SC4_COLORS[element.data.st_code_4 || 0] || '#808080'
      case 'generation':
        return SC5_COLORS[element.data.st_code_5 || 0] || '#808080'
      default:
        return '#808080'
    }
  }

  const renderElementDetails = () => {
    switch (element.type) {
      case 'pole':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <Label className="text-xs text-gray-500">Type</Label>
                <p className="font-medium">{element.data.pole_type || 'Standard'}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">Class</Label>
                <p className="font-medium">{element.data.pole_class || 'Unknown'}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">SC1 (Construction)</Label>
                <p className="font-medium">{formatStatusCode(element.data.st_code_1 || 0, 'SC1')}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">SC2 (Progress)</Label>
                <p className="font-medium">{formatStatusCode(element.data.st_code_2 || 'NA', 'SC2')}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">Location</Label>
                <p className="font-mono text-xs">
                  {element.data.lat?.toFixed(6)}, {element.data.lng?.toFixed(6)}
                </p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">UTM</Label>
                <p className="font-mono text-xs">
                  X: {element.data.utm_x?.toFixed(2)}, Y: {element.data.utm_y?.toFixed(2)}
                </p>
              </div>
            </div>
          </>
        )

      case 'connection':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <Label className="text-xs text-gray-500">Type</Label>
                <p className="font-medium">Customer Connection</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">Subnetwork</Label>
                <p className="font-medium">{element.data.subnetwork || 'Main'}</p>
              </div>
              <div className="col-span-2">
                <Label className="text-xs text-gray-500">SC3 (Connection Status)</Label>
                <p className="font-medium">{formatStatusCode(element.data.st_code_3 || 0, 'SC3')}</p>
              </div>
              {element.data.meter_serial && (
                <div className="col-span-2">
                  <Label className="text-xs text-gray-500">Meter Serial</Label>
                  <p className="font-medium">{element.data.meter_serial}</p>
                </div>
              )}
              <div>
                <Label className="text-xs text-gray-500">Location</Label>
                <p className="font-mono text-xs">
                  {element.data.lat?.toFixed(6)}, {element.data.lng?.toFixed(6)}
                </p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">UTM</Label>
                <p className="font-mono text-xs">
                  X: {element.data.utm_x?.toFixed(2)}, Y: {element.data.utm_y?.toFixed(2)}
                </p>
              </div>
            </div>
          </>
        )

      case 'conductor':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <Label className="text-xs text-gray-500">Type</Label>
                <p className="font-medium capitalize">{element.data.line_type || 'Unknown'}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">Length</Label>
                <p className="font-medium">{element.data.length?.toFixed(2) || 'N/A'} m</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">From</Label>
                <p className="font-medium">{element.data.from}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">To</Label>
                <p className="font-medium">{element.data.to}</p>
              </div>
              <div className="col-span-2">
                <Label className="text-xs text-gray-500">SC4 (Line Status)</Label>
                <p className="font-medium">{formatStatusCode(element.data.st_code_4 || 0, 'SC4')}</p>
              </div>
            </div>
          </>
        )

      case 'transformer':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <Label className="text-xs text-gray-500">Rating</Label>
                <p className="font-medium">{element.data.rating || 'N/A'} kVA</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">Pole ID</Label>
                <p className="font-medium">{element.data.pole_id || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">Location</Label>
                <p className="font-mono text-xs">
                  {element.data.lat?.toFixed(6)}, {element.data.lng?.toFixed(6)}
                </p>
              </div>
            </div>
          </>
        )

      case 'generation':
        return (
          <>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <Label className="text-xs text-gray-500">Type</Label>
                <p className="font-medium">{element.data.gen_type || 'Solar'}</p>
              </div>
              <div>
                <Label className="text-xs text-gray-500">Capacity</Label>
                <p className="font-medium">{element.data.capacity || 'N/A'} kW</p>
              </div>
              <div className="col-span-2">
                <Label className="text-xs text-gray-500">SC5 (Generation Status)</Label>
                <p className="font-medium">{formatStatusCode(element.data.st_code_5 || 0, 'SC5')}</p>
              </div>
            </div>
          </>
        )

      default:
        return null
    }
  }

  return (
    <Card className="absolute bottom-4 left-4 z-[1000] w-96 max-h-[600px] overflow-y-auto shadow-lg">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div 
              className="w-4 h-4 rounded-full" 
              style={{ backgroundColor: getStatusColor() }}
            />
            <h3 className="font-semibold capitalize">{element.type}</h3>
          </div>
          <div className="flex gap-1">
            {onEdit && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onEdit(element.data)}
                title="Edit Properties"
              >
                <Edit2 className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Editable Name */}
        <div className="mb-4">
          <Label className="text-xs text-gray-500">Name/ID</Label>
          {isEditing ? (
            <div className="flex gap-2 mt-1">
              <Input
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                className="flex-1"
                disabled={isSaving}
              />
              <Button
                size="sm"
                onClick={handleSave}
                disabled={isSaving}
              >
                <Save className="h-3 w-3" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setEditedName(element.name || element.id)
                  setIsEditing(false)
                  setError('')
                }}
                disabled={isSaving}
              >
                Cancel
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 mt-1">
              <p className="font-medium">{element.name || element.id}</p>
              {onUpdate && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsEditing(true)}
                >
                  <Edit2 className="h-3 w-3" />
                </Button>
              )}
            </div>
          )}
          {error && (
            <Alert variant="destructive" className="mt-2">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        {/* Element Details */}
        <div className="border-t pt-4">
          {renderElementDetails()}
        </div>

        {/* Raw Data (Debug) */}
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-4 border-t pt-4">
            <summary className="text-xs text-gray-500 cursor-pointer">Raw Data</summary>
            <pre className="mt-2 text-xs overflow-x-auto bg-gray-50 p-2 rounded">
              {JSON.stringify(element.data, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </Card>
  )
}
