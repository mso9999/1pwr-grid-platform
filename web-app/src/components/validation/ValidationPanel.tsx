import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, XCircle, Info, Search, Filter } from 'lucide-react'

interface ValidationPanelProps {
  site: string;
  networkData?: any;
}

interface ValidationIssue {
  id: string
  type: 'error' | 'warning' | 'info'
  category: 'pole' | 'conductor' | 'transformer' | 'customer'
  message: string
  details: string
  location: string
  timestamp: string
}

export function ValidationPanel({ site }: ValidationPanelProps) {
  const [issues, setIssues] = useState<ValidationIssue[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'error' | 'warning' | 'info'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'pole' | 'conductor' | 'transformer' | 'customer'>('all')

  useEffect(() => {
    // Fetch validation issues from backend API
    const fetchValidationResults = async () => {
      setLoading(true)
      try {
        const response = await fetch(`http://localhost:8000/api/validate/${site}`)
        const result = await response.json()
        
        if (result.success && result.results) {
          const validationIssues: ValidationIssue[] = []
          let issueId = 1
          
          // Process orphaned poles
          if (result.results.orphaned_poles?.length > 0) {
            result.results.orphaned_poles.forEach((poleId: string) => {
              validationIssues.push({
                id: String(issueId++),
                type: 'warning',
                category: 'pole',
                message: 'Orphaned pole detected',
                details: `Pole ${poleId} has no connected conductors`,
                location: poleId,
                timestamp: new Date().toISOString()
              })
            })
          }
          
          // Process invalid conductors
          if (result.results.invalid_conductors?.length > 0) {
            result.results.invalid_conductors.forEach((conductor: any) => {
              validationIssues.push({
                id: String(issueId++),
                type: 'error',
                category: 'conductor',
                message: 'Invalid conductor reference',
                details: conductor.reason || `Conductor ${conductor.id} has invalid references`,
                location: conductor.id,
                timestamp: new Date().toISOString()
              })
            })
          }
          
          // Process duplicate IDs
          if (result.results.duplicate_pole_ids?.length > 0) {
            result.results.duplicate_pole_ids.forEach((poleId: string) => {
              validationIssues.push({
                id: String(issueId++),
                type: 'error',
                category: 'pole',
                message: 'Duplicate pole ID',
                details: `Multiple poles found with ID: ${poleId}`,
                location: poleId,
                timestamp: new Date().toISOString()
              })
            })
          }
          
          // Process connectivity issues
          if (result.results.disconnected_components?.length > 1) {
            validationIssues.push({
              id: String(issueId++),
              type: 'warning',
              category: 'conductor',
              message: 'Network connectivity issue',
              details: `Network has ${result.results.disconnected_components.length} disconnected components`,
              location: 'Site-wide',
              timestamp: new Date().toISOString()
            })
          }
          
          // Add summary info
          if (result.results.statistics) {
            const stats = result.results.statistics
            validationIssues.push({
              id: String(issueId++),
              type: 'info',
              category: 'pole',
              message: 'Network statistics',
              details: `${stats.total_poles || 0} poles, ${stats.total_conductors || 0} conductors validated`,
              location: 'Site-wide',
              timestamp: new Date().toISOString()
            })
            
            if (stats.validation_rate && stats.validation_rate > 95) {
              validationIssues.push({
                id: String(issueId++),
                type: 'info',
                category: 'pole',
                message: 'High validation rate',
                details: `${stats.validation_rate.toFixed(1)}% of network elements successfully validated`,
                location: 'Site-wide',
                timestamp: new Date().toISOString()
              })
            }
          }
          
          setIssues(validationIssues)
        } else {
          // If no validation results, show a default message
          setIssues([{
            id: '1',
            type: 'info',
            category: 'pole',
            message: 'No validation issues detected',
            details: 'Network validation completed successfully with no issues found',
            location: 'Site-wide',
            timestamp: new Date().toISOString()
          }])
        }
      } catch (error) {
        console.error('Failed to fetch validation results:', error)
        setIssues([{
          id: '1',
          type: 'error',
          category: 'pole',
          message: 'Validation service unavailable',
          details: 'Unable to connect to validation service. Please ensure backend is running.',
          location: 'System',
          timestamp: new Date().toISOString()
        }])
      } finally {
        setLoading(false)
      }
    }
    
    fetchValidationResults()
  }, [site])

  const getIcon = (type: ValidationIssue['type']) => {
    switch (type) {
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const getTypeColor = (type: ValidationIssue['type']) => {
    switch (type) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-700'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-700'
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-700'
    }
  }

  const filteredIssues = issues.filter(issue => {
    const matchesType = filter === 'all' || issue.type === filter
    const matchesCategory = selectedCategory === 'all' || issue.category === selectedCategory
    const matchesSearch = searchTerm === '' || 
      issue.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      issue.details.toLowerCase().includes(searchTerm.toLowerCase()) ||
      issue.location.toLowerCase().includes(searchTerm.toLowerCase())
    
    return matchesType && matchesCategory && matchesSearch
  })

  const stats = {
    total: issues.length,
    errors: issues.filter(i => i.type === 'error').length,
    warnings: issues.filter(i => i.type === 'warning').length,
    info: issues.filter(i => i.type === 'info').length
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Validation Results</h2>
        <p className="text-sm text-gray-500 mt-1">Site: {site}</p>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Issues</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-red-50 rounded-lg border border-red-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-600">Errors</p>
              <p className="text-2xl font-bold text-red-700">{stats.errors}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-400" />
          </div>
        </div>
        <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-yellow-600">Warnings</p>
              <p className="text-2xl font-bold text-yellow-700">{stats.warnings}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-400" />
          </div>
        </div>
        <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600">Info</p>
              <p className="text-2xl font-bold text-blue-700">{stats.info}</p>
            </div>
            <Info className="w-8 h-8 text-blue-400" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search issues..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Type Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="error">Errors</option>
              <option value="warning">Warnings</option>
              <option value="info">Info</option>
            </select>
          </div>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value as any)}
            className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Categories</option>
            <option value="pole">Poles</option>
            <option value="conductor">Conductors</option>
            <option value="transformer">Transformers</option>
            <option value="customer">Customers</option>
          </select>
        </div>
      </div>

      {/* Issues List */}
      <div className="flex-1 overflow-auto">
        <div className="space-y-3">
          {filteredIssues.map((issue) => (
            <div
              key={issue.id}
              className={`bg-white rounded-lg border p-4 ${
                issue.type === 'error' ? 'border-red-200' :
                issue.type === 'warning' ? 'border-yellow-200' :
                'border-blue-200'
              }`}
            >
              <div className="flex items-start space-x-3">
                {getIcon(issue.type)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">{issue.message}</h4>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(issue.type)}`}>
                      {issue.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{issue.details}</p>
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span>📍 {issue.location}</span>
                    <span>🕐 {new Date(issue.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredIssues.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No issues found matching your filters</p>
          </div>
        )}
      </div>
    </div>
  )
}
