'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';

interface ElementEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  element: any;
  site: string;
  onElementUpdated: () => void;
}

export function ElementEditDialog({
  open,
  onOpenChange,
  element,
  site,
  onElementUpdated
}: ElementEditDialogProps) {
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (element) {
      setFormData({ ...element });
    }
  }, [element]);

  const handleSave = async () => {
    if (!element) return;
    
    setLoading(true);
    
    try {
      let endpoint = '';
      const elementType = element.type;
      const elementId = element.id;
      
      if (elementType === 'pole') {
        endpoint = `/api/network/${site}/poles/${elementId}`;
      } else if (elementType === 'connection') {
        endpoint = `/api/network/${site}/connections/${elementId}`;
      } else if (elementType === 'conductor') {
        endpoint = `/api/network/${site}/conductors/${elementId}`;
      } else {
        throw new Error('Unknown element type');
      }
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update ${elementType}`);
      }
      
      toast.success(`${elementType.charAt(0).toUpperCase() + elementType.slice(1)} updated successfully`);
      onOpenChange(false);
      onElementUpdated();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to update element: ${errorMessage}`);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (!element) return null;

  const renderPoleFields = () => (
    <>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="pole_id" className="text-right">
          Pole ID
        </Label>
        <Input
          id="pole_id"
          value={formData.pole_id || ''}
          onChange={(e) => setFormData({...formData, pole_id: e.target.value})}
          className="col-span-3"
          disabled
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="pole_type" className="text-right">
          Type
        </Label>
        <Select
          value={formData.pole_type || 'POLE'}
          onValueChange={(value) => setFormData({...formData, pole_type: value})}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="POLE">Standard Pole</SelectItem>
            <SelectItem value="KICKER">Kicker Pole</SelectItem>
            <SelectItem value="STAY">Stay Pole</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="pole_class" className="text-right">
          Class
        </Label>
        <Select
          value={formData.pole_class || 'LV'}
          onValueChange={(value) => setFormData({...formData, pole_class: value})}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="MV">Medium Voltage</SelectItem>
            <SelectItem value="LV">Low Voltage</SelectItem>
            <SelectItem value="HV">High Voltage</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="st_code_1" className="text-right">
          Status Code 1
        </Label>
        <Select
          value={String(formData.st_code_1 || 0)}
          onValueChange={(value) => setFormData({...formData, st_code_1: parseInt(value)})}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">0 - As Designed</SelectItem>
            <SelectItem value="1">1 - Updated Location</SelectItem>
            <SelectItem value="2">2 - Marked Onsite</SelectItem>
            <SelectItem value="3">3 - Consent Withheld</SelectItem>
            <SelectItem value="4">4 - Consented</SelectItem>
            <SelectItem value="5">5 - Hard Rock</SelectItem>
            <SelectItem value="6">6 - Excavated</SelectItem>
            <SelectItem value="7">7 - Pole Planted</SelectItem>
            <SelectItem value="8">8 - Poletop Dressed</SelectItem>
            <SelectItem value="9">9 - Conductor Attached</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="notes" className="text-right">
          Notes
        </Label>
        <Input
          id="notes"
          value={formData.notes || ''}
          onChange={(e) => setFormData({...formData, notes: e.target.value})}
          className="col-span-3"
          placeholder="Optional notes"
        />
      </div>
    </>
  );

  const renderConnectionFields = () => (
    <>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="pole_id" className="text-right">
          Connection ID
        </Label>
        <Input
          id="pole_id"
          value={formData.pole_id || ''}
          onChange={(e) => setFormData({...formData, pole_id: e.target.value})}
          className="col-span-3"
          disabled
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="customer_name" className="text-right">
          Customer
        </Label>
        <Input
          id="customer_name"
          value={formData.customer_name || ''}
          onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="meter_number" className="text-right">
          Meter #
        </Label>
        <Input
          id="meter_number"
          value={formData.meter_number || ''}
          onChange={(e) => setFormData({...formData, meter_number: e.target.value})}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="st_code_3" className="text-right">
          Status Code 3
        </Label>
        <Select
          value={String(formData.st_code_3 || 0)}
          onValueChange={(value) => setFormData({...formData, st_code_3: parseInt(value)})}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">0 - Planned</SelectItem>
            <SelectItem value="1">1 - Survey Complete</SelectItem>
            <SelectItem value="2">2 - Design Complete</SelectItem>
            <SelectItem value="3">3 - Materials Ready</SelectItem>
            <SelectItem value="4">4 - Under Construction</SelectItem>
            <SelectItem value="5">5 - Construction Complete</SelectItem>
            <SelectItem value="6">6 - Inspected</SelectItem>
            <SelectItem value="7">7 - Connected</SelectItem>
            <SelectItem value="8">8 - Energized</SelectItem>
            <SelectItem value="9">9 - Metered</SelectItem>
            <SelectItem value="10">10 - Commissioned</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="notes" className="text-right">
          Notes
        </Label>
        <Input
          id="notes"
          value={formData.notes || ''}
          onChange={(e) => setFormData({...formData, notes: e.target.value})}
          className="col-span-3"
          placeholder="Optional notes"
        />
      </div>
    </>
  );

  const renderConductorFields = () => (
    <>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="conductor_id" className="text-right">
          Conductor ID
        </Label>
        <Input
          id="conductor_id"
          value={formData.conductor_id || ''}
          className="col-span-3"
          disabled
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="from_pole" className="text-right">
          From Pole
        </Label>
        <Input
          id="from_pole"
          value={formData.from_pole || ''}
          className="col-span-3"
          disabled
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="to_pole" className="text-right">
          To Pole
        </Label>
        <Input
          id="to_pole"
          value={formData.to_pole || ''}
          className="col-span-3"
          disabled
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="conductor_type" className="text-right">
          Type
        </Label>
        <Select
          value={formData.conductor_type || 'LV'}
          onValueChange={(value) => setFormData({...formData, conductor_type: value})}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="MV">Medium Voltage</SelectItem>
            <SelectItem value="LV">Low Voltage</SelectItem>
            <SelectItem value="Drop">Drop Line</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="conductor_spec" className="text-right">
          Specification
        </Label>
        <Input
          id="conductor_spec"
          value={formData.conductor_spec || ''}
          onChange={(e) => setFormData({...formData, conductor_spec: e.target.value})}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="st_code_4" className="text-right">
          Status Code 4
        </Label>
        <Select
          value={String(formData.st_code_4 || 0)}
          onValueChange={(value) => setFormData({...formData, st_code_4: parseInt(value)})}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">0 - Planned</SelectItem>
            <SelectItem value="1">1 - Materials Ready</SelectItem>
            <SelectItem value="2">2 - Stringing Started</SelectItem>
            <SelectItem value="3">3 - Strung</SelectItem>
            <SelectItem value="4">4 - Tensioned</SelectItem>
            <SelectItem value="5">5 - Energized</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            Edit {element?.type?.charAt(0).toUpperCase() + element?.type?.slice(1)}
          </DialogTitle>
          <DialogDescription>
            Make changes to the {element?.type} properties below.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          {element?.type === 'pole' && renderPoleFields()}
          {element?.type === 'connection' && renderConnectionFields()}
          {element?.type === 'conductor' && renderConductorFields()}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
