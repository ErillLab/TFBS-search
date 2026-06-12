<template>
    <div class="panel">

        <div class="panel-header" @click="toggle">
        <div class="panel-header-left">
            <div class="panel-icon">
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
            <MotifFileResult
          v-if="loadedFileName"
          :file-name="loadedFileName"
          :sequences="loadedSequences"
          @clear="clearMotif"
        />

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
            <MotifFileResult
                v-if="loadedFileName"
                :file-name="loadedFileName"
                :sequences="loadedSequences"
                @clear="clearMotif"
            />

         </div>


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
import { writeToVirtualFS, readFileAsText } from '@/services/tfbsService';
import { getPyodide } from '@/services/pyodide';
import MotifFileResult from './MotifFileResult.vue';
export default{
    name: "MotifUploader",
    components: {MotifFileResult},
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
            
            loadedSequences: [],
            showSequenceList: false,

          
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
                let seqs = [];

                if (file.name.endsWith(".fa") || file.name.endsWith(".fasta") || file.name.endsWith(".jaspar")) {
                    seqs = this.parserMotif(content);
                } else {
                    seqs = content.split("\n").map(s => s.trim()).filter(Boolean);
                }

                this.loadedSequences = seqs;


                
                this.loadedFileName = file.name;
                this.$emit("motif-loaded", path)

            }
            catch(e){
                this.showStatus(this.classifyMotifError(e), false);         
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
                this.loadedSequences = sequences
                this.loadedFileName = filename;
                this.$emit("motif-loaded", path);


            } catch (e) {
                this.showStatus(e.message, false);          
            }
        },
        parserMotif(text){
            return text.split("\n").map(s => s.trim()).filter(s => s && !s.startsWith(">"));
        },
        
        clearMotif(){
            this.loadedSequences = [];
            this.showSequenceList = false;
            this.loadedFileName = null;
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
        classifyMotifError(e){
            const msg = e.message || ""
            if (msg.includes("Unsupported file format")) {
                return "The uploaded file is not in a supported format. Please upload a valid motif file."
            } else if (msg.includes("Motif file is empty")){
                return "The motif file is empty"
            } else if(msg.includes("Motif sequences must contain only")) {
                return "Invalid characters found. Only A, C, G, T are allowed."
            } else if (msg.includes("same length")) {
                return "All motif sequences must have the same length."
            } else if (msg.includes("at least 2 sequences")) {
                return "A motif must contain at least 2 sequences."
            } 

            if (msg.includes("Error creating motif")) {
                return "The motif file is not valid. Please check the sequences."
            } else if (msg.includes("Error loading sequences from text file")) {
                return "The text file does not contain a valid motif."
            }
            if (msg.includes("Unsupported file format")) {
                return "Unsupported file format. Please upload a FASTA, TXT or JASPAR motif."
            }
            const lines = msg.split("\n")
            return lines[lines.length-1].trim()
        }
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
