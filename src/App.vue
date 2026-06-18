<script>
import { RouterLink, RouterView } from 'vue-router'
import { getPyodide } from '@/services/pyodide';
import GenomeUploader from './components/GenomeUploader.vue';
import MotifUploader from './components/MotifUploader.vue';
import ParamsConfig from './components/ParamsConfig.vue';
import PipelineRunner from './components/PipelineRunner.vue';
import ResultsDownloader from './components/ResultsDownloader.vue';
import ResultsTable from './components/ResultsTable.vue';


export default{
  components: {

    GenomeUploader,
    MotifUploader,
    ParamsConfig,
    PipelineRunner,
    ResultsDownloader,
    ResultsTable,
  }, 
  data() {
    return {
      genomePath: null,
      motifPath: null,
      genome:null,
      motif:null,
      params:{},
      result: null,
      pyodideStatus: 'loading',
      pyodide: null, 
      GenomeUploaderKey: 0,
      MotifUploaderKey: 0,
      paramsKey: 0,
      isRunning: false,
      computedOperonDistance: null,
    }
  }, 
  computed: {
    pyodideLabel() {
      return { loading: 'Loading engine…', ready: 'Engine ready', error: 'Engine error' }[this.pyodideStatus]
    },
   
    },
     async mounted() {
      try {
        await getPyodide()
        this.pyodideStatus = 'ready'
      } catch {
        this.pyodideStatus = 'error'
      }
  },
  methods: {
    resetAll(){
      this.genomePath = null
      this.motifPath = null
      this.params = {}
      this.result = null
      this.genome = null
      this.motif = null
      this.GenomeUploaderKey++
      this.MotifUploaderKey++
      this.paramsKey++
    }
  }
}
</script>

<template>
  <div class="app">

    <header class="app-header">
      <div class="app-header-inner">
        <div class="app-logo">
          <i class="ti ti-dna-2" aria-hidden="true"></i>
        </div>
        <div>
          <h1 class="app-title">TFBS Search Tool</h1>
      <p class="app-subtitle">
        Transcription Factor Binding Site analysis 
      </p>
        </div>
        <div class="pyodide-indicator" :class="pyodideStatus">
          <span class="pyodide-dot"></span>
          <span class="pyodide-label">{{ pyodideLabel }}</span>
        </div>
      </div>
    </header>

    <main class="app-main">

      <div class="panels-row">
        <GenomeUploader :key="GenomeUploaderKey" :is-running="isRunning" @genome-loaded="genomePath = $event" />
        <MotifUploader :key="MotifUploaderKey" :is-running="isRunning" @motif-loaded="motifPath = $event" />
      </div>

      <ParamsConfig
        :key="paramsKey"
        :is-running="isRunning"
        :computedOperonDistance="computedOperonDistance"
        @config-params="params = $event"
      />

      <PipelineRunner

        :genome="genomePath"
        :motif="motifPath"
        :params="params"
        @operon-distance-computed="computedOperonDistance = $event"
        @pipeline-start="isRunning = $event"
        @pipeline-finished="result = $event"
        @reset-all="resetAll"
      />
     

      <ResultsDownloader
        v-if="result"
        :hits="result"
      />

      <ResultsTable
        v-if="result"
        :hits="result"
      />


    </main>

  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Sora:wght@400;500;600&display=swap');


*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
.app{
  background-color: var(--c-bg);
}
body {
  font-family: var(--mono);
  background-color: var(--c-bg);
  color: var(--c-text);
  min-height: 100vh;
}

.app-header {
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  padding: 1.25rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.app-header-inner {
  max-width: auto;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-logo {
  width: 40px; height: 40px;
  background: var(--c-tag-bg);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: var(--c-text);
  flex-shrink: 0;
}

.app-title {
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.2;
  font-family: var(--mono);
}

.app-subtitle {
  font-size: 0.75rem;
  color: var(--c-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.pyodide-indicator {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.pyodide-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.pyodide-indicator.loading .pyodide-dot { background: #ef9f27; animation: pulse 1.2s infinite; }
.pyodide-indicator.ready   .pyodide-dot { background: #639922; }
.pyodide-indicator.error   .pyodide-dot { background: #e24b4a; }

.pyodide-label {
  font-size: 0.75rem;
  font-family: var(--mono);
  color: var(--c-muted);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

.app-main {
  max-width: auto;
  margin: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
 
}

.panels-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 640px) {
  .panels-row { grid-template-columns: 1fr; }
  .app-header { padding: 1rem; }
  .app-main   { padding: 1rem; }
}
</style>