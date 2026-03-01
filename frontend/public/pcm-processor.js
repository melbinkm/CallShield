/**
 * AudioWorklet processor for accumulating PCM samples into WAV chunks.
 * First chunk: 2s for fast initial feedback. Subsequent chunks: 5s for richer analysis.
 * Replaces the deprecated ScriptProcessorNode.
 */
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._chunks = [];
    this._sampleCount = 0;
    this._chunkSamples = 16000 * 2; // First chunk: 2s for fast initial feedback
    this._fullChunkSamples = 16000 * 5; // Subsequent chunks: 5s for richer analysis
    this._firstChunkSent = false;

    // Flush remaining samples on demand (e.g. when recording stops early)
    this.port.onmessage = (e) => {
      if (e.data?.type === "flush") {
        if (this._sampleCount > 0) {
          const merged = new Float32Array(this._sampleCount);
          let offset = 0;
          for (const chunk of this._chunks) {
            merged.set(chunk, offset);
            offset += chunk.length;
          }
          this.port.postMessage(merged, [merged.buffer]);
        } else {
          // Nothing buffered — send empty signal so the caller can proceed
          this.port.postMessage(new Float32Array(0));
        }
        this._chunks = [];
        this._sampleCount = 0;
      }
    };
  }

  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel && channel.length > 0) {
      this._chunks.push(new Float32Array(channel));
      this._sampleCount += channel.length;

      if (this._sampleCount >= this._chunkSamples) {
        const merged = new Float32Array(this._sampleCount);
        let offset = 0;
        for (const chunk of this._chunks) {
          merged.set(chunk, offset);
          offset += chunk.length;
        }
        // Transfer ownership (zero-copy) to the main thread
        this.port.postMessage(merged, [merged.buffer]);
        this._chunks = [];
        this._sampleCount = 0;
        // After the first quick chunk, switch to full 5s chunks
        if (!this._firstChunkSent) {
          this._firstChunkSent = true;
          this._chunkSamples = this._fullChunkSamples;
        }
      }
    }
    return true; // Keep processor alive until explicitly stopped
  }
}

registerProcessor("pcm-processor", PCMProcessor);
