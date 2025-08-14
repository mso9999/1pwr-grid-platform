import { useEffect, useState } from 'react'
import { Activity, Users, Zap, AlertCircle } from 'lucide-react'

interface DataStatsProps {
  site: string
}

interface SiteStats {
  poles: { total: number; validated: number; validationRate: number }
  conductors: { total: number; backbone: number; distribution: number }
  customers: { total: number; connected: number; pending: number }
  transformers: { total: number; totalCapacity: number }
  validation: { issues: number; warnings: number }
}

export function DataStats({ site }: DataStatsProps) {
  const [stats, setStats] = useState<SiteStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading stats (will be replaced with API call)
    setLoading(true)
    setTimeout(() => {
      setStats({
        poles: { total: 1575, validated: 1574, validationRate: 99.9 },
        conductors: { total: 1938, backbone: 44, distribution: 1894 },
        customers: { total: 853, connected: 0, pending: 853 },
        transformers: { total: 8, totalCapacity: 1200 },
        validation: { issues: 363, warnings: 12 }
      })
      setLoading(false)
    }, 500)
  }, [site])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!stats) return null

  const statCards = [
    {
      title: 'Poles',
      value: stats.poles.total.toLocaleString(),
      subtitle: `${stats.poles.validationRate}% validated`,
      icon: Activity,
      color: 'bg-blue-500',
      detail: `${stats.poles.validated} validated`,
    },
    {
      title: 'Network Conductors',
      value: stats.conductors.total.toLocaleString(),
      subtitle: `${stats.conductors.backbone} backbone, ${stats.conductors.distribution} distribution`,
      icon: Zap,
      color: 'bg-green-500',
      detail: `${((stats.conductors.total * 50) / 1000).toFixed(1)} km total`,
    },
    {
      title: 'Customer Connections',
      value: stats.customers.total.toLocaleString(),
      subtitle: `${stats.customers.pending} pending`,
      icon: Users,
      color: 'bg-purple-500',
      detail: `${((stats.customers.connected / stats.customers.total) * 100).toFixed(1)}% connected`,
    },
    {
      title: 'Validation Issues',
      value: stats.validation.issues.toLocaleString(),
      subtitle: `${stats.validation.warnings} warnings`,
      icon: AlertCircle,
      color: stats.validation.issues > 100 ? 'bg-orange-500' : 'bg-green-500',
      detail: 'Needs review',
    },
  ]

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Network Statistics</h2>
        <p className="text-sm text-gray-500 mt-1">Site: {site}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.title} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.color} rounded-lg p-3`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
              <h3 className="text-sm font-medium text-gray-500">{stat.title}</h3>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-2">{stat.subtitle}</p>
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-600">{stat.detail}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Additional Stats */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Transformers</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Total Units</span>
              <span className="font-medium">{stats.transformers.total}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Capacity</span>
              <span className="font-medium">{stats.transformers.totalCapacity} kVA</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Average Load</span>
              <span className="font-medium">65%</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Network Health</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Voltage Drop</span>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm font-medium">
                Within limits
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Connectivity</span>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-sm font-medium">
                8 segments
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Data Quality</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium">
                99.9%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
