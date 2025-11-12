export default function LegibilityTab({ data }) {
  const { words_detected } = data

  const getLegibilityBadge = (legible) => {
    if (legible) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          ✓ Legible
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
        ✗ Not Legible
      </span>
    )
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-base font-semibold text-gray-900 mb-2">Text Recognition Results</h4>
        <p className="text-sm text-gray-600">
          Found {words_detected.length} text elements. Legible words have confidence ≥0.7 and height ≥22px.
        </p>
      </div>

      {words_detected.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>No text detected in this billboard</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Text
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Height
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Direction
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {words_detected.map((word, index) => (
                <tr key={index} className={word.legible ? '' : 'bg-red-50'}>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{word.text}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className={`text-sm font-semibold ${getConfidenceColor(word.confidence)}`}>
                      {(word.confidence * 100).toFixed(1)}%
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {word.height_px || 0}px
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {word.direction === 'rtl' ? '← RTL' : 'LTR →'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {getLegibilityBadge(word.legible)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{words_detected.length}</div>
          <div className="text-sm text-gray-500">Total Words</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {words_detected.filter(w => w.legible).length}
          </div>
          <div className="text-sm text-gray-500">Legible</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">
            {words_detected.filter(w => !w.legible).length}
          </div>
          <div className="text-sm text-gray-500">Not Legible</div>
        </div>
      </div>
    </div>
  )
}
