import { useState } from 'react'
import UploadSection from './components/UploadSection'
import EnvironmentControls from './components/EnvironmentControls'
import ResultsDashboard from './components/ResultsDashboard'
import axios from 'axios'
import { API_BASE_URL } from './config'

function App() {
  const [uploadedFile, setUploadedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [error, setError] = useState(null)

  const [environmentParams, setEnvironmentParams] = useState({
    speed_kmh: 100.0,
    view_distance_m: 40.0,
    dwell_sec: 1.0,
    lighting: 'day',
    phone_distraction: 'low'
  })

  const handleFileUpload = (file) => {
    setUploadedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setAnalysisResult(null)
    setError(null)
  }

  const handleParamChange = (param, value) => {
    setEnvironmentParams(prev => ({
      ...prev,
      [param]: value
    }))
  }

  const handleAnalyze = async () => {
    if (!uploadedFile) {
      setError('Please upload an image first')
      return
    }

    setIsAnalyzing(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)

      // Append environment parameters
      Object.keys(environmentParams).forEach(key => {
        formData.append(key, environmentParams[key])
      })

      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes timeout
      })

      setAnalysisResult(response.data)
    } catch (err) {
      console.error('Analysis error:', err)
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gradient">RecallLens</h1>
              <p className="text-sm text-gray-600 mt-1">
                Predict billboard recall at highway speeds
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">AI-Powered Analysis</div>
              <div className="text-xs text-gray-400">Computer Vision + Cognitive Science</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Upload & Controls */}
          <div className="lg:col-span-1 space-y-6">
            <UploadSection
              onFileUpload={handleFileUpload}
              previewUrl={previewUrl}
              isAnalyzing={isAnalyzing}
            />

            <EnvironmentControls
              params={environmentParams}
              onParamChange={handleParamChange}
              disabled={isAnalyzing}
            />

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={!uploadedFile || isAnalyzing}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-white text-lg shadow-lg transition-all duration-200 ${
                !uploadedFile || isAnalyzing
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl transform hover:-translate-y-0.5'
              }`}
            >
              {isAnalyzing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </span>
              ) : (
                'Analyze Billboard'
              )}
            </button>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                <p className="text-sm font-medium">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            )}
          </div>

          {/* Right Column: Results */}
          <div className="lg:col-span-2">
            {analysisResult ? (
              <ResultsDashboard
                result={analysisResult}
                originalImageUrl={previewUrl}
              />
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <div className="max-w-md mx-auto">
                  <svg className="mx-auto h-24 w-24 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h3 className="mt-4 text-lg font-medium text-gray-900">No Analysis Yet</h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Upload a billboard image and configure the environment parameters to get started.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            RecallLens uses computer vision and cognitive science to predict driver recall
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
