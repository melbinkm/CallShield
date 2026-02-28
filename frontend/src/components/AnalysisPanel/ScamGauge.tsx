interface Props {
  score: number; // 0.0 to 1.0
}

function getColor(score: number): string {
  if (score < 0.3) return "#22c55e";   // green
  if (score < 0.6) return "#eab308";   // yellow
  if (score < 0.85) return "#f97316";  // orange
  return "#ef4444";                     // red
}

export default function ScamGauge({ score }: Props) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - score * circumference;
  const color = getColor(score);
  const percentage = Math.round(score * 100);

  return (
    <div className="relative flex flex-col items-center">
      <svg width="180" height="180" className="-rotate-90">
        {/* Background circle */}
        <circle
          cx="90" cy="90" r={radius}
          fill="none" stroke="#374151" strokeWidth="12"
        />
        {/* Score arc */}
        <circle
          cx="90" cy="90" r={radius}
          fill="none" stroke={color} strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute mt-14 text-center">
        <span className="text-4xl font-bold" style={{ color }}>
          {percentage}
        </span>
        <p className="text-gray-400 text-xs mt-1">SCAM SCORE</p>
      </div>
    </div>
  );
}
