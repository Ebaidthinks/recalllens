export default function MemoryTab({ data }) {
  const { words_detected, logo_visible, brand_color_match, dominant_colors } = data

  const legibleWords = words_detected.filter(w => w.legible)
  const illegibleWords = words_detected.filter(w => !w.legible)

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-base font-semibold text-gray-900 mb-2">Memory Encoding Analysis</h4>
        <p className="text-sm text-gray-600">
          What drivers will likely encode into working memory vs. what gets forgotten.
        </p>
      </div>

      {/* What Gets Encoded */}
      <div className="space-y-3">
        <h5 className="text-sm font-semibold text-green-700 flex items-center">
          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          Likely Encoded (Remembered)
        </h5>

        <div className="bg-green-50 rounded-lg border border-green-200 p-4">
          <div className="space-y-3">
            {/* Logo */}
            <div className="flex items-start">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div className="ml-3">
                <div className="text-sm font-medium text-gray-900">Logo/Visual Identity</div>
                <div className="text-xs text-gray-600">
                  {logo_visible ? 'Logo detected and visible' : 'No logo detected'}
                </div>
              </div>
            </div>

            {/* Legible Words */}
            {legibleWords.length > 0 && (
              <div className="flex items-start">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">
                  ✓
                </div>
                <div className="ml-3">
                  <div className="text-sm font-medium text-gray-900">Legible Text ({legibleWords.length} words)</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {legibleWords.map(w => w.text).join(', ')}
                  </div>
                </div>
              </div>
            )}

            {/* Brand Colors */}
            {brand_color_match && (
              <div className="flex items-start">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">
                  ✓
                </div>
                <div className="ml-3">
                  <div className="text-sm font-medium text-gray-900">Brand Colors</div>
                  <div className="text-xs text-gray-600">
                    Strong color association detected
                  </div>
                  {dominant_colors && (
                    <div className="flex gap-2 mt-2">
                      {dominant_colors.slice(0, 5).map((color, i) => (
                        <div
                          key={i}
                          className="w-8 h-8 rounded border border-gray-300"
                          style={{ backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})` }}
                          title={`RGB(${color[0]},${color[1]},${color[2]})`}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* What Gets Forgotten */}
      {illegibleWords.length > 0 && (
        <div className="space-y-3">
          <h5 className="text-sm font-semibold text-red-700 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            Likely Forgotten (Not Encoded)
          </h5>

          <div className="bg-red-50 rounded-lg border border-red-200 p-4">
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-bold">
                  ✗
                </div>
                <div className="ml-3">
                  <div className="text-sm font-medium text-gray-900">Illegible Text ({illegibleWords.length} words)</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {illegibleWords.map(w => w.text).join(', ')}
                  </div>
                  <div className="text-xs text-red-600 mt-2">
                    Too small, too blurry, or insufficient contrast to be read at highway speeds
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Working Memory Capacity */}
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Working Memory Limits</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                Drivers can typically hold 5-7 items in working memory (Miller's Law). At {data.speed_kmh} km/h with {data.dwell_sec}s exposure, only the most salient elements get encoded.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
