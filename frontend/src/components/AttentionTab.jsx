export default function AttentionTab({ data }) {
  const { salient_regions } = data

  const getAttentionLevel = (score) => {
    if (score >= 0.7) return { label: 'High', color: 'text-green-600', bg: 'bg-green-100' }
    if (score >= 0.4) return { label: 'Medium', color: 'text-yellow-600', bg: 'bg-yellow-100' }
    return { label: 'Low', color: 'text-red-600', bg: 'bg-red-100' }
  }

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-base font-semibold text-gray-900 mb-2">Visual Attention Analysis</h4>
        <p className="text-sm text-gray-600">
          Based on ResNet50 + Grad-CAM, these are the top {salient_regions.length} areas that draw driver attention.
        </p>
      </div>

      <div className="space-y-3">
        {salient_regions.map((region, index) => {
          const level = getAttentionLevel(region.attention_score)
          return (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                    #{index + 1}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    Region at ({region.bbox[0]}, {region.bbox[1]})
                  </div>
                  <div className="text-xs text-gray-500">
                    Size: {region.bbox[2] - region.bbox[0]} × {region.bbox[3] - region.bbox[1]} px
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">
                  {(region.attention_score * 100).toFixed(1)}%
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${level.bg} ${level.color}`}>
                  {level.label}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Insight Box */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">How it works</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                We use Gradient-weighted Class Activation Mapping (Grad-CAM) with ResNet50 to predict where drivers naturally focus attention. Higher scores indicate stronger visual attraction.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
