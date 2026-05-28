<template>
  <div class="panel">
    <!-- Header -->
    <div class="panel-header" @click="open = !open">
        <div class="panel-header-left">
            <div class="panel-icon">
                <i class="ti ti-dna" aria-hidden="true"></i>
            </div>
            <span class="panel-title">Genome</span>
            <span v-if="isLoaded" class="panel-badge ok">loaded</span>
        </div>
        <i class="ti ti-chevron-down chevron" :class="{open}" aria-hidden="true"></i>
    </div>

    <div v-show="open" class="panel-body">

        <!-- Tabs -->
        <div class="method-tabs">
            <button 
            v-for="tab in tabs" :key="tab.id"
            class="method-tab"
            :class="{active: activeTab === tab.id}"
            @click="changeTabs(tab.id)"
            > {{ tab.label }}</button>
        </div>

        <!-- Tab: Upload file -->
        <div v-if="activeTab === 'file'">
            <div
            class="drop-zone" :class="{'has-file' : uploadedFiles.length}"
            @click="$refs.fileInput.click()"
            @dragover.prevent
            @drop.prevent="e => onGenomeFiles({target: e.dataTransfer})"
            >
            <i class="ti ti-upload drop-zone-icon" aria-hidden="true"></i>
            <div class="drop-zone-label">
                <strong>Click to upload</strong> or drag & drop
            </div>
            <div class="drop-zone-exts">.gb · .gbk · .genbank · .gbff</div>
            <input 
                    ref="fileInput"  type="file"
                    accept=".gb,.gbk,.genbank,.gbff"
                    multiple
                    @change="onGenomeFiles"
                    hidden
                    
                />        
            </div>

            <div v-if="uploadedFiles.length" class="file-list">
                <div v-for="(genome, index) in uploadedFiles" :key="genome.path" class="file-item">
                    <span class="file-item-name">
                        <i class="ti ti-file" aria-hidden="true"></i>
                        {{ genome.name }}
                        <!-- <span class="file-item-status"> {{ genome.status }}</span> -->
                    </span>
                    <button class="btn btn-ghost" @click="removeFile(index)" aria-label="Remove">
                        <i class="ti ti-x" aria-hidden="true"></i>
                    </button>
                </div>
            </div>
        </div>

        <div v-if="activeTab === 'accession'">
            <div class="form-group">
                <label class="form-label" for="accession-input">NCBI Accession number</label>
                <div class="input-row">
                    <input
                        id="accession-input" v-model="accessionInput"
                        class="input-text" type="text" 
                        placeholder="NC_000913.3"
                        :disabled="!isReady"
                    />
                    <button
                        class="btn btn-primary"
                        :disabled="!isReady"
                        @click="onGenomeAccessions"
                    >
                        <i v-if="loadingAccession" class="ti ti-loader-2 ti-spin"></i>
                        <span v-else>Load</span>
                    </button>
                </div>
                <p class="input-hint">Multiple accessions separated by commas</p>
            </div>
            <div v-if="uploadedAccessions.length" class="file-list">
                <div v-for="(item, index) in uploadedAccessions" :key="item.acc" class="file-item">
                    <span class="file-item-name">
                    <i class="ti ti-database"></i>
                    {{ item.acc }}
                    <!-- <span class="file-item-status">{{ item.status }}</span> -->
                    </span>

                    <button class="btn btn-ghost" @click="removeAccession(index)">
                    <i class="ti ti-x"></i>
                    </button>
                </div>
                </div>

        </div>
        <!-- <div v-if="statusMessage" class="status-toast" :class="statusOk ? 'ok' : 'error'">
            <i class="ti" :class="statusOk ? 'ti-circle-check' : 'ti-alert-circle'" aria-hidden="true"></i>
            <span>{{ statusMessage }}</span>
            <button class="toast-close" @click="statusMessage = ''" aria-label="Dismiss">
            <i class="ti ti-x" aria-hidden="true"></i>
            </button>
        </div> -->
        <transition name="toast">
        <div
            v-if="statusMessage"
            class="status-toast"
            :class="statusOk ? 'ok' : 'error'"
        >
            <i
                class="ti toast-icon"
                :class="statusOk ? 'ti-circle-check' : 'ti-alert-circle'"
                aria-hidden="true"
            ></i>

            <span class="toast-text">
                {{ statusMessage }}
            </span>
        </div>
        </transition>

        

    </div>
  </div> 

</template>

<script>
import { writeToVirtualFS, readFileAsText } from '@/services/tfbsService'
import { getPyodide } from '@/services/pyodide'

export default {
  name: 'GenomeUploader',
  emits: ['genome-loaded'],
  data() {
    return {
        open: true,
        activeTab: 'file',
        tabs: [
            { id: 'file',      label: 'Upload file' },
            { id: 'accession', label: 'Accession'   },
            {id: 'spices', label: 'Spices'}
        ],
        pyodide: null,
        uploadedFiles: [],
        uploadedAccessions: [],
        accessionInput: '',
        statusMessage: '',
        statusOk: false,
        pyodideStatus: 'loading',
        statusTimeout: null,
        loadingAccession: false
    }
  },
  async mounted() {
        try {
            this.pyodide = await getPyodide()
            this.pyodideStatus = 'ready'
        } catch (e) {
            this.pyodideStatus = 'error'
            this.pyodideError = e.message
        }
    },
  methods: {
    async onGenomeFiles(event) {
      if (!this.isReady) return
      for (const file of Array.from(event.target.files)) {
        try {
          const path = writeToVirtualFS(this.pyodide, file.name, await readFileAsText(file))
          const result = await this.pyodide.runPythonAsync(`
from tfbs.genome.loader_genomes import load_from_file
records = load_from_file(["${path}"])
`)
          this.uploadedFiles.push({ name: file.name, path, status: result })
        } catch (e) {
          this.showStatus(e.message, false)
        }
      }
      this.$emit('genome-loaded', {
        source: 'file',
        data: this.uploadedFiles.map(g => g.path)
      })
    },

    async onGenomeAccessions() {
        if (!this.isReady || !this.accessionInput.trim()) return
        this.loadingAccession = true
        this.statusMessage = ''
      
        const accessions = this.accessionInput.split(',').map(a => a.trim()).filter(a => a.length) //Abans boolean
      
        for(const acc of accessions){
            try {
            const result = await this.pyodide.runPythonAsync(`
                import json
                from tfbs.genome.loader_genomes import load_from_accession
                records = load_from_accession("${acc}")
                
            `);
            this.uploadedAccessions.push({
                acc,
                status: result > 0 ? "ok" : "empty"
            });

            this.showStatus(result, true)
        
        } catch (e) {
            this.showStatus(e.message, false)
            this.uploadedAccessions.push({
                acc,
                status: "error"
            });
        }

        }
        this.loadingAccession = false
        this.$emit('genome-loaded', { source: 'accession', data: this.uploadedAccessions.map(a => a.acc) })
      
    },
    // removeFile(index) {
    //   try { this.pyodide.FS.unlink(this.uploadedFiles[index].path) }
    //   catch { console.warn('File already removed') }
    //   this.uploadedFiles.splice(index, 1)
    //   this.$emit('genome-loaded', {
    //     source: 'file',
    //     data: this.uploadedFiles.map(g => g.path)
    //   })
    // }, 
    removeFile(index) {
  if (!this.isReady) {
    this.showStatus("Pyodide is still loading", false)
    return
  }

  try {
    this.pyodide.FS.unlink(this.uploadedFiles[index].path)
  } catch (e) {
    console.warn("FS unlink error:", e)
  }

  this.uploadedFiles.splice(index, 1)

  this.$emit('genome-loaded', {
    source: 'file',
    data: this.uploadedFiles.map(g => g.path)
  })
},


    removeAccession(index){
        this.uploadedAccessions.splice(index, 1)
        this.$emit('genome-loaded', {
            source: 'accession',
            data: this.uploadedAccessions.map(a => a.acc)
        })
    }, 
    changeTabs(tabId){
        if( tabId === 'accession' && this.uploadedFiles.length > 0){
            this.showStatus('Remove uploaded genome files before using accession mode.', false)
            return
        } else if (tabId === 'file' && this.uploadedAccessions.length > 0){
            this.showStatus('Remove loaded accessions before using file upload mode.', false)
           
            return
        }
        this.activeTab = tabId
    },
    showStatus(message, ok = true){
        this.statusMessage=message
        this.statusOk = ok;

        clearTimeout(this.statusTimeout)
        this.statusTimeout = setTimeout(() => {
            this.statusMessage = ''
        }, 3000)
    }
  }, 
  computed: {
        isReady(){
            return this.pyodideStatus == 'ready'
        }, 
        isLoaded() {
            return this.uploadedFiles.length > 0 || this.uploadedAccessions.length > 0;
        },
        hasFiles(){
            return this.uploadedFiles.length > 0
        },
        hasAccessions(){
            return this.uploadedAccessions.length > 0
        }
    }
}
</script>

<style scoped>
.ti-spin {
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>