<template>
    <div class="panel">

        <div class="panel-header" @click="toggle">
        <div class="panel-header-left">
            <div class="panel-icon">
                <!-- <i class="ti ti-timeline-event" aria-hidden="true"></i> -->
                 <i class="ti ti-grid-3x3" aria-hidden="true"></i>
            </div>
            <span class="panel-title">Motif</span>
            <span v-if="isLoaded" class="panel-badge ok">loaded</span>
        </div>
        <i class="ti ti-chevron-down chevron" :class="{open}" aria-hidden="true"></i>
    </div>

    <div v-show="open" v-if="!isRunning" class="panel-body"> 
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
            class="drop-zone" :class="{'has-file' : isLoaded}"
            @click="$refs.fileInput.click()"
            @dragover.prevent
            @drop.prevent="e => onMotifFile({target: e.dataTransfer})"
            >
            <i class="ti ti-upload drop-zone-icon" aria-hidden="true"></i>
            <div class="drop-zone-label">
                <strong>Click to upload</strong> a motif file
            </div>
            <div class="drop-zone-exts">.fasta · .fa · .txt · .jaspar</div>
            <input 
                    ref="fileInput"  type="file"
                    accept=".fasta,.fa,.txt,.jaspar"
                    @change="onMotifFile"
                    hidden
                />        
            </div>

             <div v-if="loadedFileName" class="file-list">
                <div class="file-item">
                    <span class="file-item-name">
                        <i class="ti ti-file" aria-hidden="true"></i>
                        {{ loadedFileName }}
                        <!-- <span class="file-item-status"> {{ genome.status }}</span> -->
                    </span>
                    <button class="btn btn-ghost" @click="clearMotif()" aria-label="Remove">
                        <i class="ti ti-x" aria-hidden="true"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Tab: Paste sequence -->
         <div v-if="activeTab === 'paste'">
            <div class="form-group">
                <label class="form-label" for="text_motif">Sequences (one per line)</label>
                <textarea
                    id="text_motif"
                    v-model="motifText"
                    class="input-textarea"
                    placeholder="ACGTACGT&#10;TTGTACGT&#10;ACGTACGT"
                ></textarea>
            </div>
            <button 
            class="btn btn-primary"
            :disabled="!isReady || !motifText.trim()"
            @click="onMotifText"
            >Load sequences</button>
            <div v-if="loadedFileName" class="file-list">
                <div class="file-item">
                    <span class="file-item-name">
                        <i class="ti ti-file" aria-hidden="true"></i>
                        {{ loadedFileName }}
                        <!-- <span class="file-item-status"> {{ genome.status }}</span> -->
                    </span>
                    <button class="btn btn-ghost" @click="clearMotif()" aria-label="Remove">
                        <i class="ti ti-x" aria-hidden="true"></i>
                    </button>
                </div>
            </div>
         </div>

        <!-- Status / Error -->
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




<!-- <template>
  <div class="section-block">

    <h2>Motif Upload</h2>


    <div class="upload-block">
      <label class="label">FASTA, TXT or JASPAR file:</label>
      <input 
        type="file" 
        accept=".fasta,.fa,.txt,.jaspar"
        @change="e => onMotifFile(e, 'fasta')"
        class="input-file"
      />
    </div>

    <div class="upload-block">
      <label class="label">Or paste sequences directly (one per line):</label>
    
      <textarea
        id="text_motif"
        v-model="motifText"
        rows="5"
        class="input-textarea"
        placeholder="ACGTACGT&#10;TTGTACGT&#10;ACGTACGT"
      ></textarea>

      <button 
        type="button"
        class="action-btn"
        @click="onMotifText"
        :disabled="!isReady"
      >
        Test Motif Text
      </button>
    </div>

    <pre v-if="statusMessage" :style="{ color: statusOk ? 'green' : 'red' }">
{{ statusMessage }}</pre>

  </div>
</template> -->

<script>
import { writeToVirtualFS, readFileAsText } from '@/services/tfbsService';
import { getPyodide } from '@/services/pyodide';
export default{
    name: "MotifUploader",
    emits: ['motif-loaded'],
    props: {
        isRunning: Boolean
    },
    data(){
        return{
            open: true,
            activeTab: 'file',
            tabs: [
                { id: 'file',  label: 'Upload file' },
                { id: 'paste', label: 'Paste sequences' }
            ],
            statusMessage: "",
            statusOk: false,
            pyodideStatus: 'loading',
            pyodideError: '',
            pyodide: null,
            motifText: "",
            loadedFileName: null,
            open: true,
        };
    },
    watch: {
        isRunning(newVal){
            if(newVal === true){
                this.open = false
            }
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
        async onMotifFile(event){
            this.showStatus("", false);
 
              this.motifResult = null
            if (!this.isReady) return

            const file = event.target.files[0]
            if (!file) return
            try{
                const content = await readFileAsText(file)
                const path = writeToVirtualFS(this.pyodide, file.name, content)

                const result = await this.pyodide.runPythonAsync(`
                from tfbs.motif.loader_motifs import load_motif
                motif = load_motif("${path}")
               
                `)
                this.showStatus(result, true);
                this.loadedFileName = file.name;
                this.$emit("motif-loaded", path)
            }
            catch(e){
                this.showStatus(e.message, false);         //S'hauria de posar un missatge amb els formats    
            }
        }, 
        //Text
        async onMotifText(){
            this.motifResult = null
            if (!this.isReady || !this.motifText.trim()) return

            this.showStatus("", false);          
            try {

                const sequences = this.motifText
                .split('\n')
                .map(s => s.trim().toUpperCase())
                .filter(Boolean)
                
                if (sequences.length === 0){
                    throw new Error("No sequence has been introduced.")
                }

                const dna = /^[ACGT]+$/
                const expectedLength = sequences[0].length
                for (const seq of sequences){
                    if (!dna.test(seq) || seq.length !== expectedLength) {
                        throw new Error(`Invalid sequence ${seq}. All sequences must be the same length and only the ATGC characters are allowed. `)
                    }
                }

                const filename = "motif_from_text.txt"
                const path = writeToVirtualFS(this.pyodide, filename, sequences)
                console.log(typeof(path), path)
                
                const result = await this.pyodide.runPythonAsync(`
from tfbs.motif.motif import Motif
motif = Motif.load_motif("${path}")

`)

                this.showStatus(result, true);          
                this.loadedFileName = filename;
                this.$emit("motif-loaded", path)
            } catch (e) {
                this.showStatus(e.message, false);          
            }
        },
        clearMotif(){
            this.loadedFileName = null
            this.showStatus("", false);          
            this.$emit("motif-loaded", null)
        },
        showStatus(message, ok = true){
            this.statusMessage=message
            this.statusOk = ok;

            clearTimeout(this.statusTimeout)
            this.statusTimeout = setTimeout(() => {
                this.statusMessage = ''
            }, 3000)
        },
        changeTabs(tabId){
            if(this.isLoaded){
                this.showStatus('Remove the loaded motif before switching mode.', false)
                return
            }
            this.activeTab = tabId
        },
        toggle(){
            if(!this.isRunning) {
                this.open = !this.open
            }
        },
    },
    computed: {
        isReady(){
            return this.pyodideStatus == 'ready'
        }, 
        isLoaded(){
            return !!this.loadedFileName
        }
    }
}
</script>