export default function ImageComparison({ originalUrl, simulatedUrl, heatmapUrl }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Visual Analysis</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Original */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">Original Billboard</div>
          <div className="rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
            <img
              src={originalUrl}
              alt="Original billboard"
              className="w-full h-48 object-contain"
            />
          </div>
        </div>

        {/* Simulated View */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">Driver View (Simulated)</div>
          <div className="rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
            <video
              src={simulatedUrl}
              autoPlay
              loop
              muted
              playsInline
              className="w-full h-48 object-contain"
            />
          </div>
          <p className="text-xs text-gray-500">
            Shows motion blur, atmospheric effects, and eye jitter
          </p>
        </div>

        {/* Attention Heatmap */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">Attention Heatmap</div>
          <div className="rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
            <img
              src={heatmapUrl}
              alt="Attention heatmap"
              className="w-full h-48 object-contain"
            />
          </div>
          <p className="text-xs text-gray-500">
            Red areas indicate where drivers focus attention
          </p>
        </div>
      </div>
    </div>
  )
}
