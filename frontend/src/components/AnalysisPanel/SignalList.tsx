import type { Signal } from "../../types/scamReport";

interface Props {
  signals: Signal[];
}

const severityColor = {
  low: "border-yellow-500/50 text-yellow-400",
  medium: "border-orange-500/50 text-orange-400",
  high: "border-red-500/50 text-red-400",
};

export default function SignalList({ signals }: Props) {
  if (signals.length === 0) {
    return <p className="text-gray-500 text-sm">No scam signals detected.</p>;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        Detected Signals
      </h3>
      {signals.map((signal, i) => (
        <div
          key={i}
          className={`border-l-4 pl-4 py-2 ${severityColor[signal.severity]}`}
        >
          <p className="font-medium text-sm">{signal.category}</p>
          <p className="text-gray-400 text-sm mt-1">{signal.detail}</p>
          <span className="text-xs uppercase opacity-70">{signal.severity}</span>
        </div>
      ))}
    </div>
  );
}
