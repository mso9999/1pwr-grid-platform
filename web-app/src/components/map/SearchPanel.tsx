import React, { useState } from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { SC1_COLORS, SC3_COLORS, getStatusCodeNarrative } from '@/utils/statusCodes';

interface SearchPanelProps {
  poles: any[];
  connections: any[];
  conductors: any[];
  onElementSelect: (element: any) => void;
  onClose: () => void;
}

export function SearchPanel({ 
  poles, 
  connections, 
  conductors, 
  onElementSelect, 
  onClose 
}: SearchPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [elementType, setElementType] = useState<'all' | 'pole' | 'connection' | 'conductor'>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [statusCodeFilter, setStatusCodeFilter] = useState<{
    sc1?: number
    sc2?: string
    sc3?: number
    sc4?: number
  }>({})
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const handleSearch = () => {
    let results: any[] = [];
    const query = searchQuery.toLowerCase();

    // Search poles
    if (elementType === 'all' || elementType === 'pole') {
      const poleResults = poles.filter(pole => {
        const matchesQuery = !query || 
                            pole.id.toLowerCase().includes(query) || 
                            (pole.name && pole.name.toLowerCase().includes(query));
        const matchesSC1 = statusCodeFilter.sc1 === undefined || 
                          pole.st_code_1 === statusCodeFilter.sc1;
        return matchesQuery && matchesSC1;
      }).map(pole => ({ ...pole, elementType: 'pole' }));
      results = [...results, ...poleResults];
    }

    // Search connections
    if (elementType === 'all' || elementType === 'connection') {
      const connectionResults = connections.filter(conn => {
        const matchesQuery = !query || 
                            conn.id.toLowerCase().includes(query) || 
                            (conn.customer_name && conn.customer_name.toLowerCase().includes(query));
        const matchesSC3 = statusCodeFilter.sc3 === undefined || 
                          conn.st_code_3 === statusCodeFilter.sc3;
        return matchesQuery && matchesSC3;
      }).map(conn => ({ ...conn, elementType: 'connection' }));
      results = [...results, ...connectionResults];
    }

    // Search conductors
    if (elementType === 'all' || elementType === 'conductor') {
      const conductorResults = conductors.filter(cond => {
        const matchesQuery = !query || 
                            cond.id.toLowerCase().includes(query) || 
                            (cond.name && cond.name.toLowerCase().includes(query)) ||
                            cond.from_pole?.toLowerCase().includes(query) ||
                            cond.to_pole?.toLowerCase().includes(query);
        const matchesSC4 = statusCodeFilter.sc4 === undefined || 
                          cond.st_code_4 === statusCodeFilter.sc4;
        return matchesQuery && matchesSC4;
      }).map(cond => ({ ...cond, elementType: 'conductor' }));
      results = [...results, ...conductorResults];
    }

    setSearchResults(results);
  };

  const handleResultClick = (result: any) => {
    const { elementType, ...data } = result;
    onElementSelect({
      type: elementType,
      id: result.id,
      data
    });
  };

  const getStatusColor = (result: any) => {
    if (result.elementType === 'pole') {
      return SC1_COLORS[result.st_code_1 || 0];
    } else if (result.elementType === 'connection') {
      return SC3_COLORS[result.st_code_3 || 0];
    }
    return '#808080';
  };

  return (
    <Card className="absolute top-20 left-4 z-50 w-96 max-h-[calc(100vh-120px)]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Search Network Elements</CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search Input */}
        <div className="flex gap-2">
          <Input
            placeholder="Search by ID or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button onClick={handleSearch} size="icon">
            <Search className="h-4 w-4" />
          </Button>
        </div>

        {/* Filters */}
        <div className="space-y-2">
          <div className="flex gap-2">
            <Select value={elementType} onValueChange={(value: any) => setElementType(value)}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Element type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Elements</SelectItem>
                <SelectItem value="pole">Poles Only</SelectItem>
                <SelectItem value="connection">Connections Only</SelectItem>
                <SelectItem value="conductor">Conductors Only</SelectItem>
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            >
              {showAdvancedFilters ? 'Hide' : 'Show'} Filters
            </Button>
          </div>

          {/* Advanced Status Code Filters */}
          {showAdvancedFilters && (
            <div className="space-y-2 p-3 bg-gray-50 rounded-lg">
              {elementType === 'pole' || elementType === 'all' ? (
                <Select value={statusCodeFilter.sc1?.toString() || 'all'} 
                        onValueChange={(v) => setStatusCodeFilter({...statusCodeFilter, sc1: v === 'all' ? undefined : parseInt(v)})}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="SC1 - Pole Construction" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All SC1</SelectItem>
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
              ) : null}
              
              {elementType === 'connection' || elementType === 'all' ? (
                <Select value={statusCodeFilter.sc3?.toString() || 'all'} 
                        onValueChange={(v) => setStatusCodeFilter({...statusCodeFilter, sc3: v === 'all' ? undefined : parseInt(v)})}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="SC3 - Connection Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All SC3</SelectItem>
                    <SelectItem value="0">0 - uGridNET Survey</SelectItem>
                    <SelectItem value="1">1 - Updated Location</SelectItem>
                    <SelectItem value="2">2 - Connection Fee Paid</SelectItem>
                    <SelectItem value="3">3 - Ready Board Paid</SelectItem>
                    <SelectItem value="4">4 - Contract Signed</SelectItem>
                    <SelectItem value="5">5 - DB Tested</SelectItem>
                    <SelectItem value="6">6 - Ready Board Installed</SelectItem>
                    <SelectItem value="7">7 - Cable Pulled</SelectItem>
                    <SelectItem value="8">8 - Cable Connected</SelectItem>
                    <SelectItem value="9">9 - Customer Connected</SelectItem>
                    <SelectItem value="10">10 - Energized</SelectItem>
                  </SelectContent>
                </Select>
              ) : null}
              
              {elementType === 'conductor' || elementType === 'all' ? (
                <Select value={statusCodeFilter.sc4?.toString() || 'all'} 
                        onValueChange={(v) => setStatusCodeFilter({...statusCodeFilter, sc4: v === 'all' ? undefined : parseInt(v)})}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="SC4 - Conductor Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All SC4</SelectItem>
                    <SelectItem value="0">0 - Planned</SelectItem>
                    <SelectItem value="1">1 - Material on Site</SelectItem>
                    <SelectItem value="2">2 - Stringing in Progress</SelectItem>
                    <SelectItem value="3">3 - Strung</SelectItem>
                    <SelectItem value="4">4 - Sagged and Tensioned</SelectItem>
                    <SelectItem value="5">5 - Energized</SelectItem>
                  </SelectContent>
                </Select>
              ) : null}
            </div>
          )}
        </div>

        {/* Results */}
        {searchResults.length > 0 && (
          <ScrollArea className="h-[400px] rounded-md border p-2">
            <div className="space-y-2">
              {searchResults.map((result) => (
                <div
                  key={`${result.elementType}-${result.id}`}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent cursor-pointer transition-colors"
                  onClick={() => handleResultClick(result)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {result.elementType}
                      </Badge>
                      <span className="font-medium">{result.id}</span>
                    </div>
                    {result.name && (
                      <p className="text-sm text-muted-foreground mt-1">{result.name}</p>
                    )}
                    {result.customer_name && (
                      <p className="text-sm text-muted-foreground mt-1">
                        Customer: {result.customer_name}
                      </p>
                    )}
                    {result.elementType === 'conductor' && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {result.from_pole} → {result.to_pole}
                      </p>
                    )}
                  </div>
                  <div
                    className="h-8 w-8 rounded-full"
                    style={{ backgroundColor: getStatusColor(result) }}
                    title={getStatusCodeNarrative(
                      result.elementType === 'pole' ? 'SC1' : 
                      result.elementType === 'connection' ? 'SC3' : 'SC4',
                      result.st_code_1 || result.st_code_3 || result.st_code_4 || 0
                    )}
                  />
                </div>
              ))}
            </div>
          </ScrollArea>
        )}

        {searchResults.length === 0 && searchQuery && (
          <div className="text-center py-8 text-muted-foreground">
            No results found for "{searchQuery}"
          </div>
        )}
      </CardContent>
    </Card>
  );
}
