import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, Zap, Check } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';

interface GenerationSiteEditorProps {
  site: string;
  currentPoleId?: string;
  poles: Array<{ id: string; lat: number; lng: number }>;
  onUpdate?: () => void;
}

export function GenerationSiteEditor({ 
  site, 
  currentPoleId, 
  poles,
  onUpdate 
}: GenerationSiteEditorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedPoleId, setSelectedPoleId] = useState(currentPoleId || '');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);


  const handleUpdate = async () => {
    if (!selectedPoleId) {
      setUpdateMessage({ type: 'error', text: 'Please enter a pole ID' });
      return;
    }

    // Verify pole exists
    const poleExists = poles.some(p => p.id === selectedPoleId);
    if (!poleExists) {
      setUpdateMessage({ type: 'error', text: `Pole ${selectedPoleId} not found in network` });
      return;
    }

    setIsUpdating(true);
    setUpdateMessage(null);

    try {
      const response = await fetch(`http://localhost:8000/api/network/${site}/generation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pole_id: selectedPoleId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update: ${response.statusText}`);
      }

      const data = await response.json();
      setUpdateMessage({ type: 'success', text: data.message || 'Generation site updated' });
      
      // Close dialog and trigger update callback
      setTimeout(() => {
        setIsOpen(false);
        setUpdateMessage(null);
        if (onUpdate) {
          onUpdate();
        }
      }, 1500);
    } catch (error) {
      console.error('Error updating generation site:', error);
      setUpdateMessage({ 
        type: 'error', 
        text: error instanceof Error ? error.message : 'Failed to update generation site' 
      });
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button 
          variant="outline" 
          size="sm" 
          className="gap-2"
          title="Edit Generation Site Location"
          onClick={() => {
            console.log('Edit Generation Site button clicked');
            setIsOpen(true);
          }}
        >
          <Zap className="h-4 w-4" />
          Edit Generation Site
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] z-[9999]">
        <DialogHeader>
          <DialogTitle>Edit Generation Site Location</DialogTitle>
          <DialogDescription>
            Change the generation/substation location by selecting a different pole.
            This will override the automatic detection.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="current" className="text-right">
              Current:
            </Label>
            <div className="col-span-3 text-sm text-muted-foreground">
              {currentPoleId || 'Auto-detected'}
            </div>
          </div>
          
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="pole-id" className="text-right">
              New Pole ID:
            </Label>
            <Input
              id="pole-id"
              value={selectedPoleId}
              onChange={(e) => setSelectedPoleId(e.target.value)}
              placeholder="e.g., KET_02_BB1"
              className="col-span-3"
              disabled={isUpdating}
            />
          </div>

          {updateMessage && (
            <Alert variant={updateMessage.type === 'error' ? 'destructive' : 'default'}>
              {updateMessage.type === 'error' ? (
                <AlertCircle className="h-4 w-4" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              <AlertDescription>{updateMessage.text}</AlertDescription>
            </Alert>
          )}

          <div className="text-sm text-muted-foreground">
            <p className="mb-2">Common generation site patterns:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Poles with "BB" suffix (e.g., KET_02_BB1)</li>
              <li>Poles with highest MV connectivity</li>
              <li>Poles near transformers</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => setIsOpen(false)}
            disabled={isUpdating}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleUpdate}
            disabled={isUpdating || !selectedPoleId}
          >
            {isUpdating ? 'Updating...' : 'Update Location'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
