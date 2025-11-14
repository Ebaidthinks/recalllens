import { useState, useEffect } from 'react'
import ScoreDial from './ScoreDial'
import ImageComparison from './ImageComparison'
import LegibilityTab from './LegibilityTab'
import AttentionTab from './AttentionTab'
import MemoryTab from './MemoryTab'
import FixesTab from './FixesTab'
import { API_BASE_URL } from '../config'

export default function ResultsDashboard({ result, originalImageUrl }) {
  const [activeTab, setActiveTab] = useState('legibility')

  const tabs = [
    { id: 'legibility', label: 'Legibility', icon: '📝' },
    { id: 'attention', label: 'Attention', icon: '👁️' },
    { id: 'memory', label: 'Memory', icon: '🧠' },
    { id: 'fixes', label: 'Fixes', icon: '🔧' },
  ]

  const getScoreColor = (score) => {
    if (score >= 75) return 'text-green-600'
    if (score >= 55) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreLabel = (score) => {
    if (score >= 75) return 'Excellent'
    if (score >= 55) return 'Moderate'
    return 'Poor'
  }

  return (
    <div className="space-y-6">
      {/* Score and Gist Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Score Dial */}
          <div className="flex flex-col items-center justify-center">
            <ScoreDial score={result.recall_score} />
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-500 mb-1">Recall Score</p>
              <p className={`text-2xl font-bold ${getScoreColor(result.recall_score)}`}>
                {getScoreLabel(result.recall_score)}
              </p>
            </div>
          </div>

          {/* Predicted Gist */}
          <div className="flex flex-col justify-center">
            <h3 className="text-sm font-medium text-gray-500 mb-3">Predicted Driver Recall</h3>
            <blockquote className="text-2xl font-serif italic text-gray-900 leading-relaxed border-l-4 border-blue-500 pl-4">
              "{result.predicted_gist}"
            </blockquote>
            <p className="text-sm text-gray-500 mt-4">
              What drivers will likely remember after {result.dwell_sec}s at {result.speed_kmh} km/h
            </p>
          </div>
        </div>
      </div>

      {/* Image Comparison */}
      <ImageComparison
        originalUrl={originalImageUrl}
        simulatedUrl={`${API_BASE_URL}${result.simulation_video}`}
        heatmapUrl={`${API_BASE_URL}${result.heatmap_png}`}
      />

      {/* Tabbed Analysis */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Tab Headers */}
        <div className="border-b border-gray-200">
          <div className="flex">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-4 py-4 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-b-2 border-blue-600 text-blue-600 bg-blue-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'legibility' && <LegibilityTab data={result} />}
          {activeTab === 'attention' && <AttentionTab data={result} />}
          {activeTab === 'memory' && <MemoryTab data={result} />}
          {activeTab === 'fixes' && <FixesTab data={result} />}
        </div>
      </div>

      {/* Download PDF Button */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <a
          href={`${API_BASE_URL}${result.pdf_report}`}
          download
          className="flex items-center justify-center w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg"
        >
          <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Download Full Report (PDF)
        </a>
      </div>
    </div>
  )
}
