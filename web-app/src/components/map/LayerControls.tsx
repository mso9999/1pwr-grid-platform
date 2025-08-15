'use client'

import { useState } from 'react'
import { Eye, EyeOff, Layers } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'

export interface LayerVisibility {
  poles: boolean
  connections: boolean
  mvLines: boolean
  lvLines: boolean
  dropLines: boolean
  transformers: boolean
  generation: boolean
}

interface LayerControlsProps {
  visibility: LayerVisibility
  onVisibilityChange: (visibility: LayerVisibility) => void
  counts?: {
    poles: number
    connections: number
    mvLines: number
    lvLines: number
    dropLines: number
    transformers: number
    generation: number
  }
  elementCounts?: {
    poles?: number
    connections?: number
    mvLines?: number
    lvLines?: number
    dropLines?: number
    transformers?: number
    generation?: number
  }
}

export function LayerControls({ 
  visibility, 
  onVisibilityChange,
  elementCounts = {}
}: LayerControlsProps) {
  const [isOpen, setIsOpen] = useState(true)

  const toggleLayer = (layer: keyof LayerVisibility) => {
    onVisibilityChange({
      ...visibility,
      [layer]: !visibility[layer]
    })
  }

  const toggleAll = (show: boolean) => {
    onVisibilityChange({
      poles: show,
      connections: show,
      mvLines: show,
      lvLines: show,
      dropLines: show,
      transformers: show,
      generation: show
    })
  }

  return (
    <Card className="absolute top-4 right-4 z-[1000] w-64 shadow-lg">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button 
            variant="ghost" 
            className="w-full justify-between p-3 hover:bg-gray-50"
          >
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4" />
              <span className="font-semibold">Layer Controls</span>
            </div>
            <div className="text-xs text-gray-500">
              {Object.values(visibility).filter(v => v).length}/{Object.keys(visibility).length}
            </div>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="p-3 space-y-3">
          <div className="flex justify-between gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => toggleAll(true)}
              className="flex-1"
            >
              <Eye className="h-3 w-3 mr-1" />
              Show All
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => toggleAll(false)}
              className="flex-1"
            >
              <EyeOff className="h-3 w-3 mr-1" />
              Hide All
            </Button>
          </div>

          <div className="space-y-2">
            {/* Poles */}
            <div className="flex items-center justify-between">
              <Label htmlFor="poles" className="text-sm cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span>Poles</span>
                  {elementCounts.poles !== undefined && (
                    <span className="text-xs text-gray-500">({elementCounts.poles})</span>
                  )}
                </div>
              </Label>
              <Switch 
                id="poles"
                checked={visibility.poles}
                onCheckedChange={() => toggleLayer('poles')}
              />
            </div>

            {/* Connections */}
            <div className="flex items-center justify-between">
              <Label htmlFor="connections" className="text-sm cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500" />
                  <span>Connections</span>
                  {elementCounts.connections !== undefined && (
                    <span className="text-xs text-gray-500">({elementCounts.connections})</span>
                  )}
                </div>
              </Label>
              <Switch 
                id="connections"
                checked={visibility.connections}
                onCheckedChange={() => toggleLayer('connections')}
              />
            </div>

            {/* MV Lines */}
            <div className="flex items-center justify-between">
              <Label htmlFor="mvLines" className="text-sm cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-red-600" />
                  <span>MV Lines</span>
                  {elementCounts.mvLines !== undefined && (
                    <span className="text-xs text-gray-500">({elementCounts.mvLines})</span>
                  )}
                </div>
              </Label>
              <Switch 
                id="mvLines"
                checked={visibility.mvLines}
                onCheckedChange={() => toggleLayer('mvLines')}
              />
            </div>

            {/* LV Lines */}
            <div className="flex items-center justify-between">
              <Label htmlFor="lvLines" className="text-sm cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-blue-600" />
                  <span>LV Lines</span>
                  {elementCounts.lvLines !== undefined && (
                    <span className="text-xs text-gray-500">({elementCounts.lvLines})</span>
                  )}
                </div>
              </Label>
              <Switch 
                id="lvLines"
                checked={visibility.lvLines}
                onCheckedChange={() => toggleLayer('lvLines')}
              />
            </div>

            {/* Drop Lines */}
            <div className="flex items-center justify-between">
              <Label htmlFor="dropLines" className="text-sm cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-green-600" />
                  <span>Drop Lines</span>
                  {elementCounts.dropLines !== undefined && (
                    <span className="text-xs text-gray-500">({elementCounts.dropLines})</span>
                  )}
                </div>
              </Label>
              <Switch 
                id="dropLines"
                checked={visibility.dropLines}
                onCheckedChange={() => toggleLayer('dropLines')}
              />
            </div>

            {/* Transformers */}
            <div className="flex items-center justify-between">
              <Label htmlFor="transformers" className="text-sm cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-orange-500" />
                  <span>Transformers</span>
                  {elementCounts.transformers !== undefined && (
                    <span className="text-xs text-gray-500">({elementCounts.transformers})</span>
                  )}
                </div>
              </Label>
              <Switch 
                id="transformers"
                checked={visibility.transformers}
                onCheckedChange={() => toggleLayer('transformers')}
              />
            </div>

            {/* Generation */}
            <div className="flex items-center justify-between">
              <Label htmlFor="generation" className="text-sm cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-yellow-500" />
                  <span>Generation</span>
                  {elementCounts.generation !== undefined && (
                    <span className="text-xs text-gray-500">({elementCounts.generation})</span>
                  )}
                </div>
              </Label>
              <Switch 
                id="generation"
                checked={visibility.generation}
                onCheckedChange={() => toggleLayer('generation')}
              />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}
