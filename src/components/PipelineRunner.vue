<script>
import { runTfbsPipeline } from '@/services/tfbsService';

export default{
    name: "PipelineRunner",
    props: {
        genome: {type: Object, required: true},
        motif: {type: String, required: true},
        params: {type: Object, required: true}
    }, 
    emits: ['pipeline-finished', 'reset-all', 'pipeline-start', 'operon-distance-computed'],
    data() {
        return{
            running: false,
            error: "",
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
          this.$emit('pipeline-start', true)
          try{
              const result = await runTfbsPipeline({
                  genomeSource: this.genome.source,
                  genomeData: this.genome.data,
                  motifPath: this.motif,
                  params: this.params
              });
              if(result.computedOperonDistance != null){
                this.$emit('operon-distance-computed', result.computedOperonDistance)
              }
              this.$emit("pipeline-finished", result.annotated)
          } catch(e){
              this.error = e.message;
          } finally {
              this.running = false;
              this.$emit('pipeline-start', false)

          }
        }, 
        resetAll(){
          this.$emit('reset-all')
        }
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
            </div>
        </div>
        <div v-if="running" class="run-progress">
            <div class="run-progress-bar"></div>
        </div>
        <div v-if="error" class="status-toast error" style="margin: 0 1.25rem 1.25rem;">
      <i class="ti ti-alert-circle" aria-hidden="true"></i>
      <span>{{ error }}</span>
      <button class="toast-close" @click="error = ''" aria-label="Dismiss">
        <i class="ti ti-x" aria-hidden="true"></i>
      </button>
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
.btn-reset {
  background: transparent;
  border: 1px solid var(--c-border);
  color: var(--c-muted);
  padding: 0.55rem 1rem;
  border-radius: 9px;
  font-size: 0.85rem;
}
.btn-reset:hover {
  background: var(--c-muted);
}

</style>