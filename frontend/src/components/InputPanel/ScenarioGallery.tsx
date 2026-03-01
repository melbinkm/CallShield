const SCENARIOS = [
  {
    id: "S01",
    name: "IRS Arrest Threat",
    verdict: "SCAM" as const,
    description: "Agent claims arrest warrant, demands gift card payment",
    transcript: `Caller: This is Agent Thompson from the Internal Revenue Service. Our records show you owe $3,200 in back taxes from previous years.\n\nRecipient: I'm not aware of owing anything...\n\nCaller: A warrant has been issued for your arrest. To avoid immediate detention you must settle this today. We accept payment via iTunes or Google Play gift cards. Purchase $3,200 worth and call us back immediately with the redemption codes. Do not contact your bank or attorney — this is a confidential federal matter. Officers will be dispatched to your address if we don't hear back within the hour.`,
  },
  {
    id: "S03",
    name: "Medicare Robocall",
    verdict: "SCAM" as const,
    description: "Robocall threatens Medicare benefit loss, harvests SSN",
    transcript: `Automated Voice: Important message regarding your Medicare benefits. Your coverage is about to expire. This is your final notice.\n\nPress 1 now to speak with a Medicare specialist and avoid losing your benefits immediately.\n\n[Caller presses 1]\n\nAgent: Thank you for calling Medicare services. To verify your account and prevent a lapse in coverage, I'll need your Social Security number and Medicare ID. This is urgent — your benefits will be suspended at midnight if we cannot confirm your identity today.`,
  },
  {
    id: "S05",
    name: "Grandparent Scam",
    verdict: "SCAM" as const,
    description: "Impersonates grandchild in distress, requests wire transfer",
    transcript: `Caller: Grandma? It's me, I'm in serious trouble. I was in a car accident and the police are here.\n\nRecipient: Oh no, are you hurt?\n\nCaller: I'm okay but they're saying I have to go to jail tonight unless I can post bail right now. Please don't tell Mom and Dad — I'm so embarrassed. The lawyer says I need $2,000 sent by wire transfer immediately to cover the bail bond. Please hurry, I'm really scared and I don't have much time before they take me.`,
  },
  {
    id: "L01",
    name: "Friend Catch-up",
    verdict: "SAFE" as const,
    description: "Casual reconnection call between old friends",
    transcript: `Caller: Hey! Oh my gosh, it has been so long! How are you doing these days?\n\nRecipient: I'm doing well! It's so good to hear from you.\n\nCaller: I saw your post about the new job — congratulations, that's amazing! We absolutely need to get together for coffee or lunch sometime soon. Are you free any time next weekend? I miss hanging out, we used to have so much fun. Let me know what works for your schedule!`,
  },
  {
    id: "L04",
    name: "Social Invitation",
    verdict: "SAFE" as const,
    description: "Community center staff inviting to neighborhood event",
    transcript: `Caller: Hi there, this is Sarah calling from the Riverside Community Center. I wanted to personally invite you to our annual neighborhood barbecue this coming Saturday afternoon at 2pm in the main park area.\n\nIt's a completely free event and everyone in the community is welcome. We just ask that you bring a dish to share if you're able. It's always a wonderful time to meet your neighbors. Hope to see you there! Feel free to call me back if you have any questions about parking or the menu.`,
  },
  {
    id: "L09",
    name: "Legitimate Bank Alert",
    verdict: "SAFE" as const,
    description: "Automated fraud alert about unusual transaction",
    transcript: `Automated System: This is an automated security notification from First National Bank. We have detected a transaction of $47.50 at a merchant location in another state.\n\nIf you made this purchase or recognize this charge, no action is required on your part.\n\nIf you do not recognize this transaction, please call the customer service number printed on the back of your card to dispute the charge. Please note: we will never ask for your full card number or PIN over the phone. Thank you for banking with First National Bank.`,
  },
];

interface Props {
  onTranscriptSelect: (text: string) => void;
}

export default function ScenarioGallery({ onTranscriptSelect }: Props) {
  return (
    <div className="mb-4">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        Quick Demo Scenarios
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {SCENARIOS.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => onTranscriptSelect(scenario.transcript)}
            className="text-left bg-gray-700/50 hover:bg-gray-700 border border-gray-600/50 hover:border-gray-500 rounded-lg p-3 transition-colors group"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">{scenario.id}</span>
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                scenario.verdict === "SCAM"
                  ? "bg-red-900/60 text-red-300"
                  : "bg-green-900/60 text-green-300"
              }`}>
                {scenario.verdict}
              </span>
            </div>
            <p className="text-sm font-medium text-gray-200 group-hover:text-white leading-tight mb-1">
              {scenario.name}
            </p>
            <p className="text-xs text-gray-500 leading-tight">{scenario.description}</p>
            <p className="text-xs text-blue-400 mt-2 group-hover:text-blue-300">Try this →</p>
          </button>
        ))}
      </div>
    </div>
  );
}
