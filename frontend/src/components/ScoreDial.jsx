import { useEffect, useState } from 'react'

export default function ScoreDial({ score }) {
  const [animatedScore, setAnimatedScore] = useState(0)

  useEffect(() => {
    // Animate score from 0 to actual value
    const duration = 1500 // 1.5 seconds
    const steps = 60
    const increment = score / steps
    let currentStep = 0

    const timer = setInterval(() => {
      currentStep++
      if (currentStep >= steps) {
        setAnimatedScore(score)
        clearInterval(timer)
      } else {
        setAnimatedScore(Math.round(increment * currentStep))
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [score])

  // Calculate circle parameters
  const size = 200
  const strokeWidth = 16
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (animatedScore / 100) * circumference

  // Determine color based on score
  const getColor = () => {
    if (score >= 75) return '#10b981' // green
    if (score >= 55) return '#f59e0b' // yellow
    return '#ef4444' // red
  }

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Background Circle */}
      <svg className="transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress Circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor()}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-out"
        />
      </svg>

      {/* Score Text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-5xl font-bold" style={{ color: getColor() }}>
          {animatedScore}
        </div>
        <div className="text-sm text-gray-500 font-medium">out of 100</div>
      </div>
    </div>
  )
}
