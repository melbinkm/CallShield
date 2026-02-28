interface Props {
  recommendation: string;
}

export default function RecommendationBox({ recommendation }: Props) {
  return (
    <div className="bg-gray-700/50 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-2">
        Recommendation
      </h3>
      <p className="text-gray-200 text-sm leading-relaxed">{recommendation}</p>
    </div>
  );
}
