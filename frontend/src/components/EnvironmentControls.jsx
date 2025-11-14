import { useState, useEffect } from 'react'
import { API_BASE_URL } from '../config'

export default function EnvironmentControls({ params, onParamChange, disabled }) {
  const [dubaiPresets, setDubaiPresets] = useState([])
  const [loadingPresets, setLoadingPresets] = useState(false)

  // Fetch Dubai presets on mount
  useEffect(() => {
    const fetchPresets = async () => {
      setLoadingPresets(true)
      try {
        const response = await fetch(`${API_BASE_URL}/dubai-presets`)
        const data = await response.json()
        setDubaiPresets(data.presets || [])
      } catch (error) {
        console.error('Failed to load Dubai presets:', error)
      } finally {
        setLoadingPresets(false)
      }
    }

    fetchPresets()
  }, [])

  const handlePresetChange = (presetId) => {
    if (!presetId) return

    const preset = dubaiPresets.find(p => p.id === presetId)
    if (preset) {
      // Apply all preset values
      onParamChange('speed_kmh', preset.speed_kmh)
      onParamChange('view_distance_m', preset.view_distance_m)
      onParamChange('dwell_sec', preset.dwell_sec)
      onParamChange('lighting', preset.lighting)
      onParamChange('phone_distraction', preset.phone_distraction)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Environment Parameters</h2>

      <div className="space-y-6">
        {/* Dubai Presets */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🇦🇪 Dubai Road Presets
          </label>
          <select
            onChange={(e) => handlePresetChange(e.target.value)}
            disabled={disabled || loadingPresets}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed bg-white"
            defaultValue=""
          >
            <option value="">Custom Settings</option>
            {dubaiPresets.map(preset => (
              <option key={preset.id} value={preset.id}>
                {preset.name}
              </option>
            ))}
          </select>
          {dubaiPresets.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Pre-configured for common Dubai locations
            </p>
          )}
        </div>

        {/* Speed */}
        <div>
          <label className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Speed</span>
            <span className="text-sm font-semibold text-blue-600">{params.speed_kmh} km/h</span>
          </label>
          <input
            type="range"
            min="60"
            max="140"
            step="5"
            value={params.speed_kmh}
            onChange={(e) => onParamChange('speed_kmh', parseFloat(e.target.value))}
            disabled={disabled}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>60 km/h</span>
            <span>140 km/h</span>
          </div>
        </div>

        {/* Distance */}
        <div>
          <label className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Viewing Distance</span>
            <span className="text-sm font-semibold text-blue-600">{params.view_distance_m}m</span>
          </label>
          <input
            type="range"
            min="20"
            max="60"
            step="5"
            value={params.view_distance_m}
            onChange={(e) => onParamChange('view_distance_m', parseFloat(e.target.value))}
            disabled={disabled}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>20m</span>
            <span>60m</span>
          </div>
        </div>

        {/* Dwell Time */}
        <div>
          <label className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Dwell Time</span>
            <span className="text-sm font-semibold text-blue-600">{params.dwell_sec}s</span>
          </label>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={params.dwell_sec}
            onChange={(e) => onParamChange('dwell_sec', parseFloat(e.target.value))}
            disabled={disabled}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>0.5s</span>
            <span>2.0s</span>
          </div>
        </div>

        {/* Lighting */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Lighting Conditions
          </label>
          <select
            value={params.lighting}
            onChange={(e) => onParamChange('lighting', e.target.value)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed bg-white"
          >
            <optgroup label="Standard">
              <option value="day">☀️ Day</option>
              <option value="dusk">🌆 Dusk</option>
              <option value="night">🌙 Night</option>
            </optgroup>
            <optgroup label="Dubai-Specific">
              <option value="dubai_day">☀️ Dubai Day (High Glare)</option>
              <option value="dubai_dusk">🌇 Dubai Dusk (Golden Hour)</option>
              <option value="dubai_night">✨ Dubai Night (LED Bright)</option>
            </optgroup>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Dubai options account for desert climate & LED billboards
          </p>
        </div>

        {/* Distraction */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Distraction
          </label>
          <select
            value={params.phone_distraction}
            onChange={(e) => onParamChange('phone_distraction', e.target.value)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed bg-white"
          >
            <option value="low">🟢 Low</option>
            <option value="med">🟡 Medium</option>
            <option value="high">🔴 High</option>
          </select>
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
        <p className="text-xs text-blue-800">
          <strong>Tip:</strong> Use Dubai presets for accurate local conditions, or customize parameters manually
        </p>
      </div>
    </div>
  )
}
