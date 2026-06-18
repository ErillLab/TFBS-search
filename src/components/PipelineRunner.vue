<script>
// import { runTfbsPipeline } from '@/services/tfbsService';
import { runTfbsPipelineInWorker, cancelTfbsPipeline } from '@/services/tfbsWorkerClient';
export default{
    name: "PipelineRunner",
    props: {
        genome: {type: Object, required: true},
        motif: {type: String, default: null},
        params: {type: Object, required: true}
    }, 
    emits: ['pipeline-finished', 'reset-all', 'pipeline-start', 'operon-distance-computed',],
    data() {
        return{
            running: false,
            error: "",
            result: null,
            progressMessages: [],
            showHistory: false,
        };
    }, 
    computed: {
        canRun() {
            return !!(
                this.genome?.source &&
                this.genome?.data != 0 &&
                this.motif?.trim()
            );
        },
        currentProgress(){
          return this.progressMessages[this.progressMessages.length -1] ?? '';
        },
    //     paramsSummary() {
    //         if (!this.params) return ''
    //         return `${this.params.threshold_method ?? '—'} 
    //         ${this.params.threshold_value != null ? `(${this.params.threshold_value})` : ''}
    //         · ±${this.params.margin_upstream ?? '?'}/${this.params.margin_downstream ?? '?'} bp`
    //     }
    // },
        paramsSummary() {
          if (!this.params) return ''
          const parts = [
            this.params.threshold_method ?? '—',
            `±${this.params.margin_upstream ?? '?'}/${this.params.margin_downstream ?? '?'} bp`
          ]
          if (this.params.infer_operons) {
            const dist = this.result?.metadata?.operon_distance_used
            if (dist) parts.push(`operons · ${dist} bp`)
            else if (this.params.auto_operon_distance) parts.push(`operons · auto ×${this.params.operon_distance_factor} : ${this.params.computed_operon_distance} bp` )
              
            else parts.push(`operons · ${this.params.max_distance_operon} bp`)
          }
          return parts.join(' · ')
        }
    },
    methods: {
        async runPipeline(){
          this.$emit("pipeline-finished", null)
          this.error = "";
          this.running = true;
          this.progressMessages = [];
          this.$emit('pipeline-start', true)
          try{
              const result = await runTfbsPipelineInWorker({
                  genomeSource: this.genome.source,
                  genomeData: this.genome.data,
                  motifPath: this.motif,
                  params: this.params,

                  onProgress: (msg) => {
                    // this.$emit("pipeline-progress", msg);
                    this.progressMessages.push(msg)
                  },
                  onStdout: (msg) => console.log("PY:", msg),
                  onStderr: (msg) => console.error("PY ERROR:", msg),
              });
              this.result = result;
              if(result.computedOperonDistance != null){
                this.$emit('operon-distance-computed', result.computedOperonDistance)
              }
              this.$emit("pipeline-finished", result.annotated)
          } catch(e){
            if(e.message?.includes("cancelled")) {
              this.error = "";
            } else{
              this.error = e.message;
            }
          } finally {
              this.running = false;
              this.$emit('pipeline-start', false)

          }
        }, 
        resetAll(){
          this.$emit('reset-all')
        },
        cancelPipeline(){
          cancelTfbsPipeline();
        },
    }
};
</script>

<template>
    <div class="panel run-panel">
        <div class="run-inner">
            <div v-if="canRun" class="run-info">
                <i class="ti ti-player-play" aria-hidden="true"></i>
                <div>
                    <p class="run-title">Ready to scan</p>
                    <p class="run-subtitle">Genome and motif loaded · {{ paramsSummary }}</p>
                </div>
            </div>

            <div class="run-actions">
              <button  v-if="canRun"
              class="btn btn-run"
              :disabled="!canRun || running"
              
              @click="runPipeline"
              >
              <span v-if="running" class="btn-run-spinner"></span>
              <i v-else class="ti ti-player-play" aria-hidden></i>
              {{ running ? 'Running...' : 'Run scanner' }}
              </button>
              <button class="btn btn-reset" @click="resetAll">
                <i class="ti ti-trash"></i> Reset all
              </button>
              <button v-if="running" @click="cancelPipeline" class="btn-cancel">Cancel</button>
            </div>
        </div>
        <div v-if="running" class="run-progress">
            <div class="run-progress-bar"></div>
        </div>



         <div v-if="running && progressMessages.length" class="progress-log">
      <div class="progress-log-current">
        <i class="ti ti-loader-2 ti-spin" aria-hidden="true"></i>
        <span>{{ currentProgress }}</span>
      </div>
      <div v-if="progressMessages.length > 1" class="progress-log-history-wrapper">
        <button
          class="progress-log-toggle"
          @click="showHistory = !showHistory"
        >
          <i class="ti" :class="showHistory ? 'ti-chevron-up' : 'ti-chevron-down'" aria-hidden="true"></i>
          {{ showHistory ? 'Hide' : 'Show' }} {{ progressMessages.length - 1 }} previous steps
        </button>
        <div v-if="showHistory" class="progress-log-history">
          <div
            v-for="(msg, i) in progressMessages.slice(0, -1)"
            :key="i"
            class="progress-log-item done"
          >
            <i class="ti ti-circle-check" aria-hidden="true"></i>
            <span>{{ msg }}</span>
          </div>
        </div>
      </div>
    </div>

    
    <div v-if="error" class="status-toast error" style="margin: 0 1.25rem 1.25rem;">
      <i class="ti ti-alert-circle" aria-hidden="true"></i>
      <span>{{ error }}</span>
      <button class="toast-close" @click="error = ''" aria-label="Dismiss">
        <i class="ti ti-x" aria-hidden="true"></i>
      </button>
    </div>
    <div v-if="result?.metadata && !running" class="run-metadata">
      <div v-if="result.metadata.num_hits != null" class="run-meta-item">
        <span class="run-meta-label">Hits</span>
        <span class="run-meta-value">{{ result.metadata.num_hits }}</span>
      </div>
      <div v-if="result.metadata.threshold != null" class="run-meta-item">
        <span class="run-meta-label">Threshold</span>
        <span class="run-meta-value run-meta-mono">{{ result.metadata.threshold.toFixed(4) }}</span>
      </div>
      <div v-if="result.metadata.motif_length != null" class="run-meta-item">
        <span class="run-meta-label">Motif length</span>
        <span class="run-meta-value run-meta-mono">{{ result.metadata.motif_length }} nt</span>
      </div>
      <div v-if="result.computedOperonDistance != null" class="run-meta-item">
        <span class="run-meta-label">Operon distance</span>
        <span class="run-meta-value run-meta-mono">{{ result.computedOperonDistance }} bp</span>
      </div>
    </div>
  </div>
 
</template>


<style scoped>
.run-panel { overflow: hidden; }

.run-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  flex-wrap: wrap;
}

.run-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--c-muted);
  font-size: 20px;
}

.run-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--c-text);
  line-height: 1.2;
}

.run-subtitle {
  font-size: 0.75rem;
  font-family: var(--mono);
  color: var(--c-muted);
  margin-top: 0.15rem;
}

.btn-run {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1.5rem;
  background: var(--c-text);
  color: white;
  border: none;
  border-radius: 9px;
  font-size: 0.9rem;
  font-family: var(--font);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}
.btn-run:hover:not(:disabled) { background: #3d3d3d; }
.btn-run:disabled { background: #c5c2bc; cursor: not-allowed; }

.btn-run-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.run-progress {
  height: 3px;
  background: var(--c-border);
  overflow: hidden;
}

.run-progress-bar {
  height: 100%;
  background: var(--c-text);
  animation: indeterminate 1.4s ease infinite;
  transform-origin: left;
}

@keyframes indeterminate {
  0%   { transform: scaleX(0) translateX(0); }
  50%  { transform: scaleX(0.4) translateX(120%); }
  100% { transform: scaleX(0) translateX(300%); }
}

.status-toast {
  display: flex; align-items: center; gap: 0.5rem;
  border-radius: 9px; padding: 0.6rem 0.9rem;
  font-size: 0.82rem; font-family: var(--mono);
}
.status-toast.error {
  background: var(--c-error-bg); color: var(--c-error-text);
  border: 1px solid #f09595;
}
.status-toast span { flex: 1; }
.toast-close {
  background: none; border: none; cursor: pointer;
  color: inherit; font-size: 14px; padding: 0;
}
.run-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: auto; /* empeny el bloc cap a la dreta */
}
/* .btn-reset {
  background: transparent;
  border: 1px solid var(--c-border);
  color: var(--c-muted);
  padding: 0.55rem 1rem;
  border-radius: 9px;
  font-size: 0.85rem;
}
.btn-reset:hover {
  background: var(--c-muted);
} */
.btn-reset {
  display: flex; align-items: center; gap: 0.4rem;
  background: transparent;
  border: 1px solid var(--c-border);
  color: var(--c-muted);
  padding: 0.55rem 1rem;
  border-radius: 9px;
  font-size: 0.85rem;
  font-family: var(--font);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.btn-reset:hover { border-color: #e24b4a; color: #a32d2d; }

.btn-cancel{
   display: flex; align-items: center; gap: 0.4rem;
  background: var(--c-tag-bg);;
  border: 1px solid var(--c-border);
  color: var(--c-muted);
  padding: 0.55rem 1rem;
  border-radius: 9px;
  font-size: 0.85rem;
  font-family: var(--font);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.btn-cancel:hover{ border-color: #3d3d3d;}
/* ── Progress log ── */
.progress-log {
  border-top: 1px solid var(--c-border);
  padding: 0.85rem 1.25rem;
  background: var(--c-bg);
}

.progress-log-current {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.82rem;
  font-family: var(--mono);
  color: var(--c-text);
  font-weight: 500;
}
.progress-log-current .ti { color: var(--c-muted); font-size: 15px; }

.progress-log-toggle {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.6rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.72rem;
  font-family: var(--mono);
  color: var(--c-muted);
  padding: 0;
  transition: color 0.15s;
}
.progress-log-toggle:hover { color: var(--c-text); }
.progress-log-toggle .ti { font-size: 12px; }

.progress-log-history {
  margin-top: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.progress-log-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.78rem;
  font-family: var(--mono);
  color: var(--c-muted);
}
.progress-log-item.done .ti { color: #639922; font-size: 13px; }

/* ── Error toast ── */
.status-toast {
  display: flex; align-items: center; gap: 0.5rem;
  border-radius: 9px; padding: 0.6rem 0.9rem;
  margin: 0 1.25rem 1.25rem;
  font-size: 0.82rem; font-family: var(--mono);
}
.status-toast.error {
  background: var(--c-error-bg); color: var(--c-error-text);
  border: 1px solid #f09595;
}
.status-toast span { flex: 1; }
.toast-close {
  background: none; border: none; cursor: pointer;
  color: inherit; font-size: 14px; padding: 0;
}

.run-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.9rem 1.25rem;
  border-top: 1px solid var(--c-border);
}

.run-meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 7px;
  padding: 0.25rem 0.65rem;
}
.run-meta-label {
  font-size: 0.7rem;
  color: var(--c-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.run-meta-value {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--c-text);
}
.run-meta-mono { font-family: var(--mono); }
</style>