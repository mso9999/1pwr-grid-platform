'use client';

import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Plus, 
  Cable, 
  Trash2, 
  User, 
  Scissors,
  MousePointer,
  Home
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

export type EditMode = 
  | 'select' 
  | 'add-pole' 
  | 'add-connection' 
  | 'add-conductor' 
  | 'delete' 
  | 'split-conductor';

interface MapEditToolbarProps {
  site: string;
  editMode: EditMode;
  onEditModeChange: (mode: EditMode) => void;
  selectedElement?: any;
  pendingPoleLocation?: { lat: number; lng: number } | null;
  pendingConnectionLocation?: { lat: number; lng: number } | null;
  onPoleCreated?: () => void;
  onConnectionCreated?: () => void;
  onElementUpdate?: () => void;
  onNewPole?: (pole: any) => void;
  onNewConnection?: (connection: any) => void;
}

interface PoleFormData {
  pole_id?: string;
  latitude: number;
  longitude: number;
  pole_type: string;
  pole_class: string;
  st_code_1: number;
  st_code_2: number;
  angle_class: string;
  notes?: string;
}

interface ConnectionFormData {
  connection_id?: string;
  latitude: number;
  longitude: number;
  pole_id: string;
  customer_name?: string;
  st_code_3: number;
  meter_number?: string;
  notes?: string;
}

interface ConductorFormData {
  conductor_id?: string;
  from_pole: string;
  to_pole: string;
  conductor_type: string;
  conductor_spec: string;
  length?: number;
  st_code_4: number;
  notes?: string;
}

export function MapEditToolbar({ 
  site, 
  editMode, 
  onEditModeChange, 
  selectedElement,
  pendingPoleLocation,
  pendingConnectionLocation,
  onPoleCreated,
  onConnectionCreated,
  onElementUpdate,
  onNewPole,
  onNewConnection
}: MapEditToolbarProps) {
  const [showPoleDialog, setShowPoleDialog] = useState(false);
  const [showConnectionDialog, setShowConnectionDialog] = useState(false);
  const [showConductorDialog, setShowConductorDialog] = useState(false);
  const [showSplitDialog, setShowSplitDialog] = useState(false);
  const [poleFormData, setPoleFormData] = useState<Partial<PoleFormData>>({
    pole_type: 'POLE',
    pole_class: 'LV',
    st_code_1: 0,
    st_code_2: 0,
    angle_class: 'T'
  });
  const [connectionFormData, setConnectionFormData] = useState<Partial<ConnectionFormData>>({
    st_code_3: 0
  });
  const [conductorFormData, setConductorFormData] = useState<Partial<ConductorFormData>>({
    conductor_type: 'LV',
    conductor_spec: '50',
    st_code_4: 0
  });

  // Show appropriate dialog when location is set or element selected
  useEffect(() => {
    if (pendingPoleLocation && editMode === 'add-pole') {
      setPoleFormData(prev => ({
        ...prev,
        latitude: pendingPoleLocation.lat,
        longitude: pendingPoleLocation.lng
      }));
      setShowPoleDialog(true);
    } else if (pendingConnectionLocation && editMode === 'add-connection') {
      setConnectionFormData(prev => ({
        ...prev,
        latitude: pendingConnectionLocation.lat,
        longitude: pendingConnectionLocation.lng
      }));
      setShowConnectionDialog(true);
    } else if (selectedElement && selectedElement.type === 'conductor' && editMode === 'split-conductor') {
      setShowSplitDialog(true);
    }
  }, [pendingPoleLocation, pendingConnectionLocation, editMode, selectedElement]);

  const handleCreatePole = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/network/poles/${site}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(poleFormData)
      });

      if (!response.ok) {
        throw new Error('Failed to create pole');
      }

      const result = await response.json();
      toast.success(`Pole "${result.pole_id}" created successfully`);
      
      setShowPoleDialog(false);
      setPoleFormData({
        pole_type: 'POLE',
        pole_class: 'LV',
        st_code_1: 0,
        st_code_2: 0,
        angle_class: 'T'
      });
      
      // Add the new pole to the map without reloading everything
      if (onNewPole) {
        onNewPole(result);
      }
      
      if (onPoleCreated) {
        onPoleCreated();
      }
    } catch (error) {
      toast.error('Failed to create pole');
      console.error(error);
    }
  };

  const handleCreateConnection = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/network/connections/${site}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(connectionFormData)
      });

      if (!response.ok) {
        throw new Error('Failed to create connection');
      }

      const result = await response.json();
      toast.success(`Connection "${result.connection_id}" created successfully`);
      
      setShowConnectionDialog(false);
      setConnectionFormData({
        st_code_3: 0
      });
      
      // Add the new connection to the map without reloading everything
      if (onNewConnection) {
        onNewConnection(result);
      }
      
      if (onConnectionCreated) {
        onConnectionCreated();
      }
    } catch (error) {
      toast.error('Failed to create connection');
      console.error(error);
    }
  };

  const handleCreateConductor = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/network/conductors/${site}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(conductorFormData)
      });

      if (!response.ok) {
        throw new Error('Failed to create conductor');
      }

      const result = await response.json();
      toast.success(`Conductor created successfully`);
      
      setShowConductorDialog(false);
      setConductorFormData({
        conductor_type: 'LV',
        conductor_spec: '50',
        st_code_4: 0
      });
      
      if (onElementUpdate) {
        onElementUpdate();
      }
    } catch (error) {
      toast.error('Failed to create conductor');
      console.error(error);
    }
  };

  const handleSplitConductor = async (action: 'split' | 'trim-start' | 'trim-end') => {
    if (!selectedElement) return;
    
    try {
      const conductorId = selectedElement.id;
      
      // For now, just show a message - actual implementation would need backend support
      if (action === 'split') {
        toast.info(`Split conductor ${conductorId} at midpoint - Backend implementation pending`);
      } else if (action === 'trim-start') {
        toast.info(`Trim conductor ${conductorId} from start - Backend implementation pending`);
      } else {
        toast.info(`Trim conductor ${conductorId} from end - Backend implementation pending`);
      }
      
      // Reset edit mode
      onEditModeChange('select');
      
      // Would call backend API here when implemented
      // const response = await fetch(`/api/network/${site}/conductors/${conductorId}/${action}`, { method: 'POST' });
      
    } catch (error) {
      console.error('Error splitting conductor:', error);
      toast.error('Failed to split conductor');
    }
  };

  const handleDelete = async () => {
    if (!selectedElement) return;
    
    try {
      const elementType = selectedElement.type;
      const elementId = selectedElement.id;
      
      // Determine API endpoint based on element type
      let endpoint = '';
      if (elementType === 'pole') {
        endpoint = 'poles';
      } else if (elementType === 'connection') {
        endpoint = 'connections';
      } else if (elementType === 'conductor') {
        endpoint = 'conductors';
      } else {
        toast.error('Unknown element type');
        return;
      }
      
      const response = await fetch(
        `http://localhost:8000/api/network/${site}/${endpoint}/${elementId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        throw new Error(`Failed to delete ${elementType}`);
      }

      toast.success(`${elementType.charAt(0).toUpperCase() + elementType.slice(1)} deleted successfully`);
      
      // Reset edit mode and refresh map
      onEditModeChange('select');
      if (onElementUpdate) {
        onElementUpdate();
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to delete element: ${errorMessage}`);
      console.error(error);
    }
  };

  return (
    <>
      <div className="map-edit-toolbar bg-white rounded-lg shadow-lg p-2 flex items-center space-x-2">
        <div className="text-sm font-medium px-2 py-1">Edit Tools</div>
        
        <Button
          variant={editMode === 'select' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onEditModeChange('select')}
          className="w-full justify-start"
        >
          <MousePointer className="h-4 w-4 mr-2" />
          Select
        </Button>

        <Button
          variant={editMode === 'add-pole' ? 'default' : 'outline'}
          size="sm"
          onClick={() => {
            onEditModeChange('add-pole');
            toast.info('Click on map to place pole');
          }}
          className="w-full justify-start"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Pole
        </Button>

        <Button
          variant={editMode === 'add-connection' ? 'default' : 'outline'}
          size="sm"
          onClick={() => {
            onEditModeChange('add-connection');
            toast.info('Click on map to place connection');
          }}
          className="w-full justify-start"
        >
          <Home className="h-4 w-4 mr-2" />
          Add Connection
        </Button>

        <Button
          variant={editMode === 'add-conductor' ? 'default' : 'outline'}
          size="sm"
          onClick={() => {
            onEditModeChange('add-conductor');
            setShowConductorDialog(true);
          }}
          className="w-full justify-start"
        >
          <Cable className="h-4 w-4 mr-2" />
          Add Conductor
        </Button>

        <Button
          variant={editMode === 'split-conductor' ? 'default' : 'outline'}
          size="sm"
          onClick={() => {
            onEditModeChange('split-conductor');
            toast.info('Click on a conductor to split or trim');
          }}
          className="w-full justify-start"
        >
          <Scissors className="h-4 w-4 mr-2" />
          Split/Trim Conductor
        </Button>

        <Button
          variant={editMode === 'delete' ? 'destructive' : 'outline'}
          size="sm"
          onClick={() => {
            if (editMode === 'delete' && selectedElement) {
              handleDelete();
            } else {
              onEditModeChange('delete');
              toast.info('Click on an element to delete');
            }
          }}
          className="w-full justify-start"
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Delete
        </Button>
      </div>

      {/* Pole Creation Dialog */}
      <Dialog open={showPoleDialog} onOpenChange={setShowPoleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Pole</DialogTitle>
            <DialogDescription>
              Enter details for the new pole
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="pole_id" className="text-right">
                Pole ID
              </Label>
              <Input
                id="pole_id"
                value={poleFormData.pole_id || ''}
                onChange={(e) => setPoleFormData({...poleFormData, pole_id: e.target.value})}
                className="col-span-3"
                placeholder="Auto-generated if empty"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="pole_type" className="text-right">
                Type
              </Label>
              <Select
                value={poleFormData.pole_type}
                onValueChange={(value) => setPoleFormData({...poleFormData, pole_type: value})}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="POLE">Pole</SelectItem>
                  <SelectItem value="TOWER">Tower</SelectItem>
                  <SelectItem value="SUBSTATION">Substation</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="pole_class" className="text-right">
                Class
              </Label>
              <Select
                value={poleFormData.pole_class}
                onValueChange={(value) => setPoleFormData({...poleFormData, pole_class: value})}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="LV">Low Voltage</SelectItem>
                  <SelectItem value="MV">Medium Voltage</SelectItem>
                  <SelectItem value="HV">High Voltage</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="angle_class" className="text-right">
                Angle Class
              </Label>
              <Select
                value={poleFormData.angle_class}
                onValueChange={(value) => setPoleFormData({...poleFormData, angle_class: value})}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="T">Terminal</SelectItem>
                  <SelectItem value="I">Intermediate</SelectItem>
                  <SelectItem value="A">Angle</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="notes" className="text-right">
                Notes
              </Label>
              <Textarea
                id="notes"
                value={poleFormData.notes || ''}
                onChange={(e) => setPoleFormData({...poleFormData, notes: e.target.value})}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPoleDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreatePole}>Create Pole</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Connection Creation Dialog */}
      <Dialog open={showConnectionDialog} onOpenChange={setShowConnectionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Connection</DialogTitle>
            <DialogDescription>
              Enter details for the new customer connection
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="pole_id_conn" className="text-right">
                Pole ID
              </Label>
              <Input
                id="pole_id_conn"
                value={connectionFormData.pole_id || ''}
                onChange={(e) => setConnectionFormData({...connectionFormData, pole_id: e.target.value})}
                className="col-span-3"
                placeholder="Associated pole ID"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="customer_name" className="text-right">
                Customer
              </Label>
              <Input
                id="customer_name"
                value={connectionFormData.customer_name || ''}
                onChange={(e) => setConnectionFormData({...connectionFormData, customer_name: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="meter_number" className="text-right">
                Meter #
              </Label>
              <Input
                id="meter_number"
                value={connectionFormData.meter_number || ''}
                onChange={(e) => setConnectionFormData({...connectionFormData, meter_number: e.target.value})}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConnectionDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateConnection}>Create Connection</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Conductor Creation Dialog */}
      <Dialog open={showConductorDialog} onOpenChange={setShowConductorDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Conductor</DialogTitle>
            <DialogDescription>
              Connect two poles with a conductor
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="from_pole" className="text-right">
                From Pole
              </Label>
              <Input
                id="from_pole"
                value={conductorFormData.from_pole || ''}
                onChange={(e) => setConductorFormData({...conductorFormData, from_pole: e.target.value})}
                className="col-span-3"
                placeholder="Starting pole ID"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="to_pole" className="text-right">
                To Pole
              </Label>
              <Input
                id="to_pole"
                value={conductorFormData.to_pole || ''}
                onChange={(e) => setConductorFormData({...conductorFormData, to_pole: e.target.value})}
                className="col-span-3"
                placeholder="Ending pole ID"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="conductor_type" className="text-right">
                Type
              </Label>
              <Select
                value={conductorFormData.conductor_type}
                onValueChange={(value) => setConductorFormData({...conductorFormData, conductor_type: value})}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="LV">Low Voltage</SelectItem>
                  <SelectItem value="MV">Medium Voltage</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="conductor_spec" className="text-right">
                Spec
              </Label>
              <Select
                value={conductorFormData.conductor_spec}
                onValueChange={(value) => setConductorFormData({...conductorFormData, conductor_spec: value})}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25mm²</SelectItem>
                  <SelectItem value="35">35mm²</SelectItem>
                  <SelectItem value="50">50mm²</SelectItem>
                  <SelectItem value="70">70mm²</SelectItem>
                  <SelectItem value="95">95mm²</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConductorDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateConductor}>Create Conductor</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Split Conductor Dialog */}
      <Dialog open={showSplitDialog} onOpenChange={setShowSplitDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Split/Trim Conductor</DialogTitle>
            <DialogDescription>
              Choose how to modify the selected conductor
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex flex-col gap-4">
              <Button
                onClick={() => {
                  if (selectedElement) {
                    handleSplitConductor('split');
                    setShowSplitDialog(false);
                  }
                }}
                className="w-full"
              >
                <Scissors className="h-4 w-4 mr-2" />
                Split at Midpoint
              </Button>
              <Button
                onClick={() => {
                  if (selectedElement) {
                    handleSplitConductor('trim-start');
                    setShowSplitDialog(false);
                  }
                }}
                variant="outline"
                className="w-full"
              >
                Trim from Start
              </Button>
              <Button
                onClick={() => {
                  if (selectedElement) {
                    handleSplitConductor('trim-end');
                    setShowSplitDialog(false);
                  }
                }}
                variant="outline"
                className="w-full"
              >
                Trim from End
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
