export default function FixesTab({ data }) {
  const { suggestions } = data

  const getImpactBadge = (impact) => {
    const match = impact.match(/\+(\d+)/)
    if (!match) return null

    const points = parseInt(match[1])
    let color = 'bg-gray-100 text-gray-800'
    if (points >= 15) color = 'bg-green-100 text-green-800'
    else if (points >= 10) color = 'bg-yellow-100 text-yellow-800'
    else color = 'bg-orange-100 text-orange-800'

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${color}`}>
        {impact}
      </span>
    )
  }

  const getPriorityIcon = (index) => {
    if (index === 0) return '🔥'
    if (index === 1) return '⚡'
    if (index === 2) return '💡'
    return '📌'
  }

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-base font-semibold text-gray-900 mb-2">Actionable Recommendations</h4>
        <p className="text-sm text-gray-600">
          Prioritized fixes to improve driver recall. Impact estimates show predicted score increase.
        </p>
      </div>

      {suggestions.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-6xl mb-3">🎉</div>
          <p className="text-lg font-medium text-gray-900">Excellent Billboard!</p>
          <p className="text-sm text-gray-600 mt-1">No critical issues detected</p>
        </div>
      ) : (
        <div className="space-y-3">
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className="bg-white rounded-lg border-2 border-gray-200 p-5 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">{getPriorityIcon(index)}</div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900">
                      Priority {index + 1}
                    </div>
                  </div>
                </div>
                {getImpactBadge(suggestion.impact)}
              </div>

              <div className="ml-11">
                <h5 className="text-base font-semibold text-gray-900 mb-2">
                  {suggestion.title}
                </h5>
                <p className="text-sm text-gray-700 mb-3">
                  {suggestion.description}
                </p>

                {/* Action Items */}
                {suggestion.action_items && suggestion.action_items.length > 0 && (
                  <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
                    <div className="text-xs font-semibold text-blue-900 mb-2">ACTION ITEMS:</div>
                    <ul className="space-y-1">
                      {suggestion.action_items.map((item, i) => (
                        <li key={i} className="text-sm text-blue-800 flex items-start">
                          <span className="mr-2">→</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Implementation Guide */}
      {suggestions.length > 0 && (
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-900">Implementation Priority</h3>
              <div className="mt-2 text-sm text-blue-800">
                <p>
                  Start with the highest impact recommendations. Each fix has been tested to improve recall scores based on cognitive science and real-world billboard performance data.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
