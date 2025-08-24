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
  onNewConductor?: (conductor: any) => void;
  onElementDeleted?: (element: { id: string; type: string }) => void;
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
  onNewConnection,
  onNewConductor,
  onElementDeleted
}: MapEditToolbarProps) {
  const [isPoleDialogOpen, setPoleDialogOpen] = useState(false)
  const [isConnectionDialogOpen, setConnectionDialogOpen] = useState(false)
  const [isConductorDialogOpen, setConductorDialogOpen] = useState(false)
  const [isDeleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [showSplitDialog, setShowSplitDialog] = useState(false);
  const [poleFormData, setPoleFormData] = useState({
    pole_id: '',
    latitude: 0,
    longitude: 0,
    pole_type: 'POLE',
    pole_class: 'LV',
    st_code_1: 0,
    st_code_2: 'NA',
    angle_class: '0-15',
    notes: ''
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
    console.log('=== MapEditToolbar useEffect ===', { pendingPoleLocation, editMode });
    if (pendingPoleLocation && editMode === 'add-pole') {
      console.log('=== Opening pole dialog ===', pendingPoleLocation);
      setPoleFormData(prev => ({
        ...prev,
        latitude: pendingPoleLocation.lat,
        longitude: pendingPoleLocation.lng
      }));
      setPoleDialogOpen(true);
      console.log('=== Pole dialog state set to true ===');
      // Force a DOM check
      setTimeout(() => {
        const modal = document.querySelector('[data-pole-modal]');
        console.log('=== Modal in DOM ===', modal ? 'Found' : 'Not found');
      }, 100);
    } else if (pendingConnectionLocation && editMode === 'add-connection') {
      setConnectionFormData(prev => ({
        ...prev,
        latitude: pendingConnectionLocation.lat,
        longitude: pendingConnectionLocation.lng
      }));
      setConnectionDialogOpen(true);
    } else if (selectedElement && selectedElement.type === 'conductor' && editMode === 'split-conductor') {
      setShowSplitDialog(true);
    }
  }, [pendingPoleLocation, pendingConnectionLocation, editMode, selectedElement]);

  const handleCreatePole = async () => {
    try {
      console.log('=== Sending pole data ===', JSON.stringify(poleFormData, null, 2));
      
      const response = await fetch(`http://localhost:8000/api/network/poles/${site}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(poleFormData)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('=== API Error Response ===', {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`Failed to create pole: ${response.status} ${errorText}`);
      }

      const result = await response.json();
      toast.success(`Pole "${result.pole.pole_id}" created successfully`);
      
      setPoleDialogOpen(false);
      setPoleFormData({
        pole_id: '',
        latitude: 0,
        longitude: 0,
        pole_type: 'POLE',
        pole_class: 'LV',
        st_code_1: 0,
        st_code_2: 'NA',
        angle_class: '0-15',
        notes: ''
      });
      
      // Add the new pole to the map without reloading everything
      if (onNewPole && result.pole) {
        onNewPole(result.pole);
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
      toast.success(`Connection "${result.connection.connection_id}" created successfully`);
      
      setConnectionDialogOpen(false);
      setConnectionFormData({
        st_code_3: 0
      });
      
      // Add the new connection to the map without reloading everything
      if (onNewConnection && result.connection) {
        onNewConnection(result.connection);
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
      
      setConductorDialogOpen(false);
      setConductorFormData({
        conductor_type: 'LV',
        conductor_spec: '50',
        st_code_4: 0
      });
      
      // Add the new conductor to the map without reloading everything
      if (onNewConductor && result.conductor) {
        onNewConductor(result.conductor);
      }
      
      if (onElementUpdate) {
        onElementUpdate(); // Kept for now as a fallback
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

  const performDelete = async (force = false) => {
    if (!selectedElement) return

    const { type: elementType, id: elementId } = selectedElement
    let url = `/api/network/${elementType}s/${site}/${elementId}`

    if (elementType === 'pole' && force) {
      url += '?force=true'
    }

    try {
      const response = await fetch(url, { method: 'DELETE' })
      const result = await response.json()

      if (response.ok) {
        toast.success(result.message || `${elementType} deleted successfully.`)
        if (onElementDeleted) {
          onElementDeleted({ id: elementId, type: elementType })
        }
        setDeleteConfirmOpen(false)
      } else {
        if (response.status === 409 && elementType === 'pole' && result.detail?.includes('connected conductors')) {
          setDeleteConfirmOpen(true)
        } else {
          toast.error(result.detail || 'Failed to delete element.')
        }
      }
    } catch (error) {
      console.error(`Failed to delete ${elementType}:`, error)
      toast.error(`An error occurred while deleting the ${elementType}.`)
    }
  }

  const handleDelete = () => {
    if (!selectedElement) {
      toast.error('No element selected for deletion.')
      return
    }
    performDelete(false)
  }

  return (
    <>
      <div className="map-edit-toolbar bg-white rounded-lg shadow-lg p-2 flex items-center space-x-2 absolute top-4 left-[60px] z-50">
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
            setConductorDialogOpen(true);
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
          variant="destructive"
          onClick={handleDelete}
          disabled={!selectedElement}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Delete Selected
        </Button>
      </div>

      {/* Confirmation Dialog for Force Deleting Poles */}
      <Dialog open={isDeleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Force Delete</DialogTitle>
            <DialogDescription>
              This pole has connected conductors. Deleting it will also delete all associated conductors. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={() => performDelete(true)}>
              Force Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialogs for creating elements */}
      {isPoleDialogOpen && (
        <div 
          data-pole-modal
          className="fixed inset-0 z-[9999] bg-black/50 flex items-center justify-center"
          onClick={() => setPoleDialogOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 9999,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <div 
            className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold mb-4">Create New Pole</h2>
            <p className="text-sm text-gray-600 mb-4">Enter details for the new pole</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Pole ID</label>
                <input 
                  type="text"
                  className="w-full border rounded px-3 py-2"
                  placeholder="Auto-generated if empty"
                  value={poleFormData.pole_id || ''}
                  onChange={(e) => setPoleFormData({...poleFormData, pole_id: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Latitude</label>
                <input 
                  type="number"
                  className="w-full border rounded px-3 py-2"
                  value={poleFormData.latitude}
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Longitude</label>
                <input 
                  type="number"
                  className="w-full border rounded px-3 py-2"
                  value={poleFormData.longitude}
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Pole Type</label>
                <select 
                  className="w-full border rounded px-3 py-2"
                  value={poleFormData.pole_type}
                  onChange={(e) => setPoleFormData({...poleFormData, pole_type: e.target.value})}
                >
                  <option value="POLE">POLE</option>
                  <option value="STRUCTURE">STRUCTURE</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Pole Class</label>
                <select 
                  className="w-full border rounded px-3 py-2"
                  value={poleFormData.pole_class}
                  onChange={(e) => setPoleFormData({...poleFormData, pole_class: e.target.value})}
                >
                  <option value="LV">LV</option>
                  <option value="MV">MV</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Status Code 1 (Construction Progress)</label>
                <select 
                  className="w-full border rounded px-3 py-2"
                  value={poleFormData.st_code_1}
                  onChange={(e) => setPoleFormData({...poleFormData, st_code_1: parseInt(e.target.value)})}
                >
                  <option value={0}>0: uGridNET output (as designed)</option>
                  <option value={1}>1: Updated planned location</option>
                  <option value={2}>2: Marked with label onsite</option>
                  <option value={3}>3: Consent withheld</option>
                  <option value={4}>4: Consented</option>
                  <option value={5}>5: Hard Rock</option>
                  <option value={6}>6: Excavated</option>
                  <option value={7}>7: Pole planted</option>
                  <option value={8}>8: Poletop dressed</option>
                  <option value={9}>9: Conductor attached</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Status Code 2 (Further Progress)</label>
                <select 
                  className="w-full border rounded px-3 py-2"
                  value={poleFormData.st_code_2}
                  onChange={(e) => setPoleFormData({...poleFormData, st_code_2: e.target.value})}
                >
                  <option value="NA">NA: None</option>
                  <option value="SP">SP: Stay wires planned</option>
                  <option value="SI">SI: Stay wires installed</option>
                  <option value="KP">KP: Kicker pole planned</option>
                  <option value="KI">KI: Kicker pole installed</option>
                  <option value="TP">TP: Transformer planned</option>
                  <option value="TI">TI: Transformer installed</option>
                  <option value="TC">TC: Transformer commissioned</option>
                  <option value="MP">MP: Meter planned</option>
                  <option value="MI">MI: Meter installed</option>
                  <option value="MC">MC: Meter commissioned</option>
                  <option value="EP">EP: Earth planned</option>
                  <option value="EI">EI: Earth installed</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Angle Class</label>
                <select 
                  className="w-full border rounded px-3 py-2"
                  value={poleFormData.angle_class}
                  onChange={(e) => setPoleFormData({...poleFormData, angle_class: e.target.value})}
                >
                  <option value="0-15">0-15° (Straight/minimal angle)</option>
                  <option value="15-30">15-30° (Small angle)</option>
                  <option value="30-45">30-45° (Medium angle)</option>
                  <option value="45-60">45-60° (Large angle)</option>
                  <option value="60-90">60-90° (Sharp angle)</option>
                  <option value="90+">90°+ (Dead end/termination)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea 
                  className="w-full border rounded px-3 py-2 h-20"
                  value={poleFormData.notes || ''}
                  onChange={(e) => setPoleFormData({...poleFormData, notes: e.target.value})}
                  placeholder="Optional notes..."
                />
              </div>
              <div className="flex gap-2 pt-4">
                <button 
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  onClick={handleCreatePole}
                >
                  Create Pole
                </button>
                <button 
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                  onClick={() => setPoleDialogOpen(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <Dialog open={false} onOpenChange={setPoleDialogOpen}>
        <DialogContent className="z-[9999] max-w-md" style={{zIndex: 9999, position: 'fixed'}}>
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
            <Button variant="outline" onClick={() => setPoleDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreatePole}>Create Pole</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Connection Creation Dialog */}
      <Dialog open={isConnectionDialogOpen} onOpenChange={setConnectionDialogOpen}>
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
            <Button variant="outline" onClick={() => setConnectionDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateConnection}>Create Connection</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Conductor Creation Dialog */}
      <Dialog open={isConductorDialogOpen} onOpenChange={setConductorDialogOpen}>
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
            <Button variant="outline" onClick={() => setConductorDialogOpen(false)}>
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
