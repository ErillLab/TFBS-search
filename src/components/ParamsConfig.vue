<script>
export default{
    name: "ParamsConfig", 
    emits: ["config-params"],
    props: {
        isRunning: Boolean,
        computedOperonDistance: {type: Number, default: null}
    },
    data() {
        return{
          open: false,
          bgMode: 'uniform',
          bgCustom: {A: 0.25, C: 0.25, G: 0.25, T: 0.25},

          pseudocount: 0.01,
          thresholdMethod: "direct",
          thresholdValue: 1,
          background: null,
          integration_log: false,
          marginUpstream: 250,
          marginDownstream: 50,
          inferOperons: false,
          max_distance_operon: 100,
          doubleReport: true,
          open: true, 

          autoOperonDistance: false,
          operonDistanceFactor: 1.0,
          factorOptions: [0.5, 0.75, 1, 1.5, 2, 3],
        }
    },
    computed:{
        showThresholdValue(){
            return this.thresholdMethod !== "patser";
        },
        thresholdMax(){
            if (["fpr", "fnr", "balanced"].includes(this.thresholdMethod)) return 1
            return null
        }, 
        thresholdValueHint(){
          if (this.thresholdMethod === 'fpr') return 'Acceptable false positive rate (0-1). Example: 0.01 = 1%.'
          else if (this.thresholdMethod === 'fnr') return 'Acceptable false negative rate (0-1).'
          else if (this.thresholdMethod === 'balanced') return 'Balanced point between FPR and FNR (0-1).'
          return 'Miminum raw score to report a hit.'
        }, 
        operonModeHint(){
          if(this.autoOperonDistance) return ''
        },
        rangeBarStyle() {
          const totalLeft = 500
          const totalRight = 200
          const total = totalLeft + totalRight
          const left = ((totalLeft - this.marginUpstream) / total) * 100
          const right = ((totalRight - this.marginDownstream) / total) * 100
          return {
            left: `${left}%`,
            right: `${right}%`
          }
        },
        bgSum(){
          return Object.values(this.bgCustom).reduce((a,b) => a + (b || 0), 0)
        }, 
        bgSumOk() {
          return Math.abs(this.bgSum -1 ) < 0.01
        }
    }, 
    watch: {
      isRunning(newVal){
        if(newVal === true){
            this.open = false
        }
      },
      thresholdMethod(newMethod){
        if (["fpr", "fnr", "balanced"].includes(newMethod)){
          if(this.thresholdValue > 1)
                this.thresholdValue = 1;
        }
        this.emitParams();
      }, 
      thresholdValue(newValue){
        if (["fpr", "fnr", "balanced"].includes(this.thresholdMethod) && newValue > 1) {
          this.thresholdValue = 1;
        }
        this.emitParams();

      },
      pseudocount: "emitParams",
      // thresholdValue: "emitParams",
      background: "emitParams",
      integration_log: "emitParams",
      marginUpstream: "emitParams",
      marginDownstream: "emitParams",
      inferOperons: "emitParams",
      max_distance_operon: "emitParams",
      doubleReport: "emitParams",
      autoOperonDistance: "emitParams",
      operonDistanceFactor: "emitParams",
      computedOperonDistance: "emitParams"

    },
    mounted() {
        this.emitParams();
    },
    methods: {
      openParam() {
        if(!this.isRunning){
          this.open = !this.open
        }
        
        if(this.open) {
          this.$nextTick(() => {
            this.$el.scrollIntoView({ behavior: 'smooth', block: 'start'})
          })
        }
      },
      syncBackground(){
        this.background = this.bgSumOk ? {...this.bgCustom} : null
        this.emitParams()
      },

      emitParams(){
        this.$emit("config-params", {
            pseudocount: this.pseudocount,
            threshold_method: this.thresholdMethod,
            threshold_value:
                this.thresholdMethod === "patser" ? null : this.thresholdValue,
            background: this.background,
            integration_log: this.integration_log,
            margin_upstream: this.marginUpstream,
            margin_downstream: this.marginDownstream,
            infer_operons: this.inferOperons,
            max_distance_operon: this.inferOperons ? this.max_distance_operon : null,
            double_report: this.doubleReport,
            auto_operon_distance: this.autoOperonDistance,
            operon_distance_factor: this.operonDistanceFactor,
            computed_operon_distance: this.computedOperonDistance,

          });
      },
      
    }
};   
</script>

<template>
  <div class="panel params-panel">

    <!-- Header -->
    <div class="panel-header" @click="openParam">
    <div class="panel-header-left">
      <div class="panel-icon">
        <i class="ti ti-adjustments-horizontal" aria-hidden="true"></i>
      </div>
      <span class="panel-title">Pipeline Parameters</span>
      <span class="panel-badge">{{ thresholdMethod }} · ±{{ marginUpstream }}/{{ marginDownstream }} bp</span>
      <!-- <span class="panel-badge" v-if="autoOperonDistance">{{ operonDistanceFactor }}x  <span v-if="computedOperonDistance > 0"> · {{ computedOperonDistance }} bp</span> </span> -->
    </div>
    <i class="ti ti-chevron-down chevron" :class="{open}" aria-hidden="true"></i>
    </div>

    <div v-show="open" v-if="!isRunning" class="panel-body params-body" ref="paramsBody">
      <div class="params-grid">
        <!-- Scoring -->
        <section class="param-section">
          <h3 class="param-section-title">
            <i class="ti ti-chart-bar" aria-hidden="true"></i> Scoring
          </h3>
          <div class="param-field">
            <div class="param-label-row">
              <label class="form-label" for="pseudocount">Pseudocount</label>
              <span class="param-tooltip" data-tip="Small value added to each count to avoid zero probabilities in the frequency matrix.">
                <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>
            <input 
              id="pseudocount"
              type="number" 
              step="0.001" 
              min="0"
              v-model.number="pseudocount"
              class="input-text input-narrow"
            />
          </div>

          <div class="param-field">
            <div class="param-label-row">
              <label class="form-label" for="threshold-method">Threshold method</label>
              <span class="param-tooltip" data-tip="How the score cutoff is determined.  Direct uses a raw score; FPR/FNR use error rates; Patser uses its own statistical model.">
              <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>
            <select id="threshold-method" v-model="thresholdMethod" class="input-text">
              <option value="direct">Direct (raw score)</option>
              <option value="fpr">False Positive Rate (FPR)</option>
              <option value="fnr">False Negative Rate (FNR)</option>
              <option value="balanced">Balanced</option>
              <option value="patser">Patser</option>
            </select>
          </div>
          <div v-if="showThresholdValue" class="param-field">
          <div class="param-label-row">
            <label class="form-label" for="threshold-value">Threshold value</label>
            <span class="param-tooltip" :data-tip="thresholdValueHint">
              <i class="ti ti-info-circle" aria-hidden="true"></i>
            </span>
          </div>
            <input
              id="threshold-value"
              type="number"
              step="0.0001"
              v-model.number="thresholdValue"
              :max="thresholdMax"
              class="input-text input-narrow"
            />
          </div>

          <div class="param-field">
            <div class="param-label-row">
              <label class="form-label">Strand score integration</label>
              <span class="param-tooltip" data-tip="How forward and reverse strand scores are combined into a single site score. Max takes the best strand; Log-sum uses a log₂ approximation that rewards hits on both strands simultaneously.">
                <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>
            <div class="background-tabs">
              <button
                class="bg-tab" :class="{ active: !integration_log }"
                @click="integration_log = false"
              >
                <i class="ti ti-arrow-up" aria-hidden="true"></i> Max
              </button>
              <button
                class="bg-tab" :class="{ active: integration_log }"
                @click="integration_log = true"
              >
                <i class="ti ti-math-function" aria-hidden="true"></i> Log-sum
              </button>
            </div>
          </div>
        </section>

        <section class="param-section">
          <h3 class="param-section-title">
            <i class="ti ti-arrows-left-right" aria-hidden="true"></i>Regulatory window
          </h3>
          <div class="param-field">
            <div class="param-label-row">
              <label class="form-label">Region arround TLS</label>
              <span class="param-tooltip" data-tip="Distance upstream (5') and downstream (3') from the transcription start site to consider as promoter region.">
                <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>

            <div class="range-visual">
              <div class="range-track-wrapper">
                <div class="range-axis">
                  <span class="range-axis-label upstream">5' upstream</span>
                  <span class="range-axis-label tss">TSS</span>
                  <span class="range-axis-label downstream">3' downstream</span>
                </div>
                <div class="range-bar-container">
                  <div class="range-bar-fill" :style="rangeBarStyle"></div>
                  <div class="range-tss-marker"></div>
                </div>
              </div>
              <div class="range-inputs-row">
                <div class="range-input-group">
                  <span class="range-badge upstream-badge">–{{ marginUpstream }} bp</span>
                  <input
                    type="range" min="0" max="500" step="10"
                    v-model.number="marginUpstream"
                    class="range-slider range-slider-upstream"
                    :style="{ direction: 'rtl' }"
                  >
                </div>
                <div class="range-input-group">
                  <input
                    type="range" min="0" max="200" step="5"
                    v-model.number="marginDownstream"
                    class="range-slider range-slider-downstream"
                  >
                  <span class="range-badge downstream-badge">+{{ marginDownstream }} bp</span>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section class="param-section">
          <h3 class="param-section-title">
            <i class="ti ti-dna-2" aria-hidden="true"></i> Annotation
          </h3>

          <div class="param-field">
            <div class="param-label-row">
              <label class="form-label">Operon inference</label>
              <span class="param-tooltip" data-tip="Group consecutive co-directional genes into operons when they are closer than the maximum operon distance.">
                <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="inferOperons">
              <span class="toggle-track">
                <span class="toggle-thumb"></span>
              </span>
              <span class="toggle-label">{{ inferOperons ? 'Enabled' : 'Disabled' }}</span>
            </label>
          </div>

          <div v-if="inferOperons" class="param-field">
            <div class="param-label-row">
              <label class="form-label" for="max-operon">Max operon distance</label>
              <span class="param-tooltip" :data-tip="autoOperonDistance ?  
              'The maximum operon distance is automatically estimated as the average intergenic distance between genes multiplied by the selected factor.' :
              'Maximum intergenic distance (bp) between consecutive genes to be considered part of the same operon.'">
                <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>

            <label class="toggle-switch" style="margin-bottom: 0.75rem;">
            <input type="checkbox" v-model="autoOperonDistance">
            <span class="toggle-track">
              <span class="toggle-thumb"></span>
            </span>
            <span class="toggle-label">{{ autoOperonDistance ? 'Auto' : 'Manual' }}</span>
          </label>

            <div v-if="autoOperonDistance" class="operon-auto-block">
              <div class="chip-group">
                <button
                  v-for="f in factorOptions" :key="f"
                  class="chip"
                  :class="{ active: operonDistanceFactor === f }"
                  @click="operonDistanceFactor = f"
                >{{ f }}×</button>
              </div>
              <p v-if="computedOperonDistance" class="input-hint" style="margin-top: 0.5rem;">
                <i class="ti ti-arrow-right" aria-hidden="true" style="font-size:11px; margin-right:3px;"></i>
                estimated {{ computedOperonDistance }} bp
              </p>
            </div>
            <div v-else class="input-with-unit">
              <input
                id="max-operon"
                type="number"
                v-model.number="max_distance_operon"
                class="input-text input-narrow"
              >
              <span class="input-unit">bp</span>
            </div>
          </div>

          <div class="param-field">
            <div class="param-label-row">
              <label class="form-label">Gene attribution</label>
              <span class="param-tooltip" data-tip="If a site is associated with multiple genes (e.g., divergent regions), report one row per gene. Disable to report only the primary association.">
                <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="doubleReport">
              <span class="toggle-track">
                <span class="toggle-thumb"></span>
              </span>
              <span class="toggle-label">{{ doubleReport ? 'All associations' : 'Single association' }}</span>
            </label>
          </div>

          <!-- Background -->
          <div class="param-field">
            <div class="param-label-row">
              <label class="form-label">Background model</label>
              <span class="param-tooltip" data-tip="Nucleotide background frequencies {A, C, G, T} that sum to 1. Leave empty to use uniform (0.25 each). Example: {&quot;A&quot;:0.3,&quot;C&quot;:0.2,&quot;G&quot;:0.2,&quot;T&quot;:0.3}">
                <i class="ti ti-info-circle" aria-hidden="true"></i>
              </span>
            </div>
            <div class="background-tabs">
              <button
                class="bg-tab" :class="{ active: bgMode === 'uniform' }"
                @click="bgMode = 'uniform'; background = null"
              >Uniform</button>
              <button
                class="bg-tab" :class="{ active: bgMode === 'custom' }"
                @click="bgMode = 'custom'"
              >Custom</button>
            </div>
            <div v-if="bgMode === 'custom'" class="bg-custom-inputs">
              <div v-for="nuc in ['A','C','G','T']" :key="nuc" class="bg-nuc-field">
                <label class="bg-nuc-label">{{ nuc }}</label>
                <input
                  type="number" step="0.01" min="0" max="1"
                  v-model.number="bgCustom[nuc]"
                  @input="syncBackground"
                  class="input-text input-nuc"
                >
              </div>
              <span class="bg-sum-indicator" :class="bgSumOk ? 'ok' : 'warn'">
                Σ = {{ bgSum.toFixed(2) }}
              </span>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>    
</template>


<style scoped>
/* ── Layout ── */
.params-body { padding: 1.5rem; }

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
}

.param-section {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.param-section-title {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--c-muted);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--c-border);
}

.param-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.param-label-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

/* ── Tooltip ── */
.param-tooltip {
  position: relative;
  cursor: help;
  color: var(--c-muted);
  font-size: 14px;
}
.param-tooltip::after {
  content: attr(data-tip);
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: #1a1a1a;
  color: #f5f4f0;
  font-size: 0.73rem;
  font-family: var(--font);
  line-height: 1.5;
  padding: 0.45rem 0.7rem;
  border-radius: 7px;
  width: 220px;
  white-space: normal;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 10;
}
.param-tooltip:hover::after { opacity: 1; }

/* ── Helpers reutilitzables locals ── */
.input-narrow { max-width: 140px; }

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.input-unit {
  font-size: 0.78rem;
  color: var(--c-muted);
  font-family: var(--mono);
}

/* ── Toggle switch ── */
.toggle-switch {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  width: fit-content;
}
.toggle-switch input { display: none; }
.toggle-track {
  width: 36px; height: 20px;
  background: var(--c-border);
  border-radius: 20px;
  position: relative;
  transition: background-color 0.2s;
  flex-shrink: 0;
}
.toggle-switch input:checked + .toggle-track { background: #1a1a1a; }
.toggle-thumb {
  position: absolute;
  top: 3px; left: 3px;
  width: 14px; height: 14px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
}
.toggle-switch input:checked + .toggle-track .toggle-thumb {
  transform: translateX(16px);
}
.toggle-label { font-size: 0.82rem; color: var(--c-muted); }

/* ── Regulatory window ── */
.range-visual {
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: 10px;
  padding: 1rem;
}
.range-axis {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}
.range-axis-label {
  font-size: 0.68rem;
  font-family: var(--mono);
  color: var(--c-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.range-bar-container {
  height: 8px;
  background: var(--c-border);
  border-radius: 4px;
  position: relative;
  margin-bottom: 0.9rem;
}
.range-bar-fill {
  position: absolute;
  top: 0; bottom: 0;
  background: #1a1a1a;
  border-radius: 4px;
  transition: left 0.1s, right 0.1s;
}
.range-tss-marker {
  position: absolute;
  top: -3px;
  left: calc(500 / 700 * 100%);
  width: 2px; height: 14px;
  background: #c5822a;
  border-radius: 1px;
}
.range-inputs-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
.range-input-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
}

.range-slider {
  flex: 1;
  accent-color: #1a1a1a;
  cursor: pointer;
  width: 100%;
  min-width: 0;
}
@media (max-width: 1200px) {
  .range-inputs-row {
    flex-direction: column;
    align-items: stretch;
  }

  .range-input-group {
    width: 100%;
  }
}
.range-badge {
  font-size: 0.72rem;
  font-family: var(--mono);
  font-weight: 500;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.upstream-badge   { background: #e6f1fb; color: #0c447c; }
/* .downstream-badge { background: #eaf3de; color: #27500a; } */
.downstream-badge {
  background: #e6f6ef;
  color: #1f5a3a;
}
.operon-badge {background: #fff1e6;  color: #7a3b00; }

/* ── Background model ── */
.background-tabs {
  display: flex;
  gap: 0.3rem;
  margin-bottom: 0.5rem;
}
.bg-tab {
  padding: 0.3rem 0.8rem;
  font-size: 0.78rem;
  font-family: var(--font);
  font-weight: 500;
  border: 1px solid var(--c-border);
  border-radius: 7px;
  background: none;
  color: var(--c-muted);
  cursor: pointer;
  transition: all 0.15s;
}
.bg-tab.active { background: #1a1a1a; color: white; border-color: #1a1a1a; }

.bg-custom-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;

  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}
.bg-nuc-field { display: flex; align-items: center; gap: 0.25rem; }
.bg-nuc-label {
  font-size: 0.78rem;
  font-family: var(--mono);
  font-weight: 600;
  width: 12px;
}
/* .input-nuc { width: 62px !important; max-width: 62px; text-align: center; } */
.input-nuc {
  width: 100% !important;
  min-width: 90px;
  text-align: center;
  padding: 0.45rem 0.6rem;
}
.bg-sum-indicator {
  font-size: 0.72rem;
  font-family: var(--mono);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  margin-left: auto;
}
.bg-sum-indicator.ok   { background: var(--c-success-bg); color: var(--c-success-text); }
.bg-sum-indicator.warn { background: #faeeda; color: #633806; }

/* ── Chip group ── */
.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.chip {
  padding: 0.25rem 0.65rem;
  font-size: 0.78rem;
  font-family: var(--mono);
  font-weight: 500;
  border: 1px solid var(--c-border);
  border-radius: 20px;
  width: 55px;
  text-align: center;
  background: none;
  color: var(--c-muted);
  cursor: pointer;
  transition: all 0.15s;
}
.chip:hover { border-color: var(--c-border-focus); color: var(--c-text); }
.chip.active {
  background: var(--c-text);
  color: white;
  border-color: var(--c-text);
}
</style>