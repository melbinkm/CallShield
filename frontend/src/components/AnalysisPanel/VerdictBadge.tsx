import type { Verdict } from "../../types/scamReport";

interface Props {
  verdict: Verdict;
}

const verdictStyles: Record<Verdict, { bg: string; text: string; label: string }> = {
  SAFE:        { bg: "bg-green-500/20", text: "text-green-400", label: "SAFE" },
  SUSPICIOUS:  { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "SUSPICIOUS" },
  LIKELY_SCAM: { bg: "bg-orange-500/20", text: "text-orange-400", label: "LIKELY SCAM" },
  SCAM:        { bg: "bg-red-500/20", text: "text-red-400", label: "SCAM" },
};

export default function VerdictBadge({ verdict }: Props) {
  const style = verdictStyles[verdict];
  return (
    <span className={`inline-block px-4 py-2 rounded-full text-sm font-bold ${style.bg} ${style.text}`}>
      {style.label}
    </span>
  );
}
