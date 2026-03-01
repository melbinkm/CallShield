import TabSelector from "./TabSelector";
import AudioUploader from "./AudioUploader";
import TranscriptPaster from "./TranscriptPaster";
import MicRecorder from "./MicRecorder";
import ScenarioGallery from "./ScenarioGallery";

type Tab = "upload" | "record" | "paste";

interface ChunkData {
  scam_score?: number;
  confidence?: number;
  [key: string]: unknown;
}

interface Props {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  onFileSelect: (file: File) => void;
  onTranscriptSubmit: (text: string) => void;
  disabled?: boolean;
  isRecording?: boolean;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  cumulativeScore?: number;
  verdict?: string;
  recommendation?: string;
  audioLevel?: number;
  hasResults?: boolean;
  latestChunk?: ChunkData;
  chunks?: ChunkData[];
  onTranscriptSelect?: (text: string) => void;
  prefillText?: string;
}

export default function InputPanel({
  activeTab,
  onTabChange,
  onFileSelect,
  onTranscriptSubmit,
  disabled,
  isRecording,
  onStartRecording,
  onStopRecording,
  cumulativeScore,
  verdict,
  recommendation,
  audioLevel,
  hasResults,
  latestChunk,
  chunks,
  onTranscriptSelect,
  prefillText,
}: Props) {
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <TabSelector activeTab={activeTab} onTabChange={onTabChange} />
      <div className="p-6">
        <ScenarioGallery onTranscriptSelect={onTranscriptSelect || (() => {})} />
        {activeTab === "upload" && (
          <AudioUploader onFileSelect={onFileSelect} disabled={disabled} />
        )}
        {activeTab === "record" && (
          <MicRecorder
            isRecording={isRecording || false}
            onStart={onStartRecording || (() => {})}
            onStop={onStopRecording || (() => {})}
            cumulativeScore={cumulativeScore}
            verdict={verdict}
            recommendation={recommendation}
            audioLevel={audioLevel}
            hasResults={hasResults}
            latestChunk={latestChunk}
            chunks={chunks}
          />
        )}
        {activeTab === "paste" && (
          <TranscriptPaster onTranscriptSubmit={onTranscriptSubmit} disabled={disabled} prefillText={prefillText} />
        )}
      </div>
    </div>
  );
}
