<template>
  <div class="panel">
    <!-- Header -->
    <div class="panel-header" @click="toggle">
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
                <strong>Click to upload</strong> genome files
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
            <div v-if="uploadedAccessions.length " class="file-list">
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
        <!-- <div v-if="activeTab === 'species'">
            <SpeciesSearch :disables="!isReady"
            @confirmed="onSpeciesConfirmed"
            @species-uploaded = "uploadedSpecies = $event"
            />
        </div> -->
        <div v-if="activeTab === 'species'">
            <div class="form-group">
                <label class="form-label">Species name</label>
                <div class="input-row">
                    <input 
                    type="text"
                    v-model="speciesQuery"
                    class="input-text"
                    placeholder="Escherichia coli"
                    :disabled="loadingSpecies"
                    @keyup.enter="searchSpecies">

                    <button class="btn btn-primary" :disabled="loadingSpecies || !speciesQuery.trim()"
                    @click="searchSpecies">
                        <i v-if="loadingSpecies" class="ti ti-loader-2 ti-spin"></i>
                        <span v-else> Search</span>
                    </button>
                </div>
                <p class="input-hint"> Searches NCBI reference geomes (RefSeq)</p>
            </div>

            <div v-if="uploadedSpecies.length" class="file-list">
                <div v-for="(item, index) in uploadedSpecies" :key="item.assemblyAccession">
                    <div class="file-item">        
                        <span class="file-item-name">
                            <i class="ti ti-dna"></i>
                            <span> {{ item.organismName }}</span>
                            <span style="font-size: 11px; color: var(--color--text-secondary); margin-left: 4px;">
                                {{ item.assemblyAccession }} · {{ item.count }} sequences
                            </span>
                        </span>
                        <div style="display:flex; gap: 4px; align-items:center;">
                             <button 
                                class="btn btn-ghost" 
                                @click="expandedSpecies[item.assemblyAccession] = !expandedSpecies[item.assemblyAccession]"
                                :title="expandedSpecies[item.assemblyAccession] ? 'Hide sequences' : 'Show sequences'"
                            >
                                <i class="ti" :class="expandedSpecies[item.assemblyAccession] ? 'ti-chevron-up' : 'ti-chevron-down'"></i>
                            </button>
                            <button class="btn btn-ghost" @click="removeSpecies(index)" aria-label="Remove">
                                <i class="ti ti-x"></i>
                            </button>
                        </div>
                    </div>
                    <div v-if="expandedSpecies[item.assemblyAccession]" class="accession-sublist">
                        <div 
                            v-for="acc in item.accessions" 
                            :key="acc" 
                            class="accession-subitem"
                        >
                            <i class="ti ti-dna-off" style="font-size:11px; color: var(--color--text-secondary)"></i>
                            <span>{{ acc }}</span>
                        </div>
                    </div>
                </div>
                    
            </div>
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

        <!-- Modal assemblies -->
        <teleport to="body">
            <div
                v-if="showSpeciesModal"
                class="modal-backdrop"
                @click.self="closeSpeciesModal()"
            >
                <div class="modal">
                    <div class="modal-header">
                        <div>
                            <p class="modal-title"> Referece assemblies</p>
                            <p class="modal-subtitle">
                                {{ speciesAssemblies.length }} results for <em> {{ speciesQuery }}</em>.
                            </p>
                        </div>
                        <button class="btn btn-ghost" @click="closeSpeciesModal()" aria-label="Close">
                            <i class="ti ti-x"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div
                        v-for="a in speciesAssemblies"
                        :key="a.accession"
                        class="modal-item"
                        :class="{selected: speciesSelected?.accession == a.accession}"
                        @click="speciesSelected = a"
                        >
                            <div class="modal-item-row">
                                <i class="ti" :class="speciesSelected?.accession === a.accession ? 'ti-circle-check' : 'ti-dna'"></i>
                                <span class="modal-item-accession">{{ a.accession }}</span> <p> | </p>
                                <span>{{ a.organismName }}</span>
                                <span v-if="a.refseqCategory" class="badge badge-ref">{{ a.refseqCategory }}</span>
                                <span class="badge badge-level">{{ a.assemblyLevel }}</span>
                            </div>
                            <p class="modal-item-meta">
                                {{ a.assemblyName }} · {{ a.submitter }} ·
                                {{ a.releaseDate }} · {{ a.chromosomeCount }} seqs
                            </p>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <span class="input-hint" style="margin: 0;">
                            {{ speciesSelected ? 'All sequences will be loaded' : 'Click an assembly to select it' }}
                        </span>
                        <button class="btn btn-primary" :disabled="!speciesSelected || loadingSpecies"
                        @click="confirmSpecies(speciesSelected)">
                        <i v-if="loadingSpecies" class="ti ti-loader-2 ti-spin"></i>
                        <span v-else>Confirm selected</span>
                        </button>
                    </div>
                </div>
        
            </div>
        </teleport>


        

    </div>
  </div> 

</template>

<script>
import { writeToVirtualFS, readFileAsText } from '@/services/tfbsService'
import { getPyodide } from '@/services/pyodide'
import { searchAssemblies, getSequenceReports } from '@/services/ncbiDatasetService.js';
// import SpeciesSearch from './SpeciesSearch.vue';

export default {
    name: 'GenomeUploader',
    emits: ['genome-loaded'],
    props: {
        isRunning: {type: Boolean, required: true}
    },
    data() {
        return {
            open: true,
            activeTab: 'file',
            tabs: [
                { id: 'file',      label: 'Upload file' },
                { id: 'accession', label: 'Accession'   },
             {id: 'species', label: 'Species'}
            ],
            pyodide: null,
            uploadedFiles: [],
            uploadedAccessions: [],
            accessionInput: '',
            statusMessage: '',
            statusOk: false,
            pyodideStatus: 'loading',
            statusTimeout: null,
            loadingAccession: false,
            mes: "",
            open: true,
            expandedSpecies:{},

            speciesQuery: '',
            uploadedSpecies: [],
            speciesAssemblies: [], 
            speciesSelected: null,
            loadingSpecies: false,
            showSpeciesModal: false
        }
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
                this.showStatus(this.classifyGenomeError(e), false)
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
                    records
                    
                `);
                const records = result.toJs ? result.toJs() : result
                console.log(records)
                const isEmpty = !records || (Array.isArray(records) && records.length === 0)
                console.log("isEmpty", isEmpty)

                if (isEmpty) {
                    this.showStatus(`Accession "${acc}" is not valid or no data found`, false)
                    // this.uploadedAccessions.push({ acc, status: "error" })
                    console.log("dins de l'if")
                } else {
                    this.uploadedAccessions.push({ acc, status: "ok" })
                    this.showStatus(`Accession "${acc}" loaded successfully`, true) //no se si deixar-ho !!
                }
                // this.uploadedAccessions.push({
                //     acc,
                //     status: result > 0 ? "ok" : "empty"
                // });

                // this.showStatus(result, true)
            
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
        onSpeciesConfirmed({ accessions, assemblyName }) {
            for (const acc of accessions) {
                if (!this.uploadedAccessions.find(a => a.acc === acc)) {
                this.uploadedAccessions.push({ acc, status: 'ok' })
                }
            }
            this.$emit('genome-loaded', {
                source: 'accession',
                data: this.uploadedAccessions.map(a => a.acc)
            })
            console.log(`Added ${accessions.length} sequences from ${assemblyName}`, true)
        },
        async searchSpecies(){
            if(!this.speciesQuery.trim()) return
            this.loadingSpecies = true
            try{
                this.speciesAssemblies = await searchAssemblies(this.speciesQuery)
                if(!this.speciesAssemblies.length){
                    this.showStatus(`No reference assemblies found for "${this.speciesQuery}"`, false)
                    return
                }
                this.showSpeciesModal = true //obre menu de resultats
            } catch(e){
                this.showStatus(e.message, false)
            } finally {
                this.loadingSpecies = false
            }
        },
        async confirmSpecies(assembly){
            this.expandedSpecies[assembly.accession] = false
            this.loadingSpecies = true
            try{
                const sequences = await getSequenceReports(assembly.accession)
                const accessions = sequences.map(s => s.accession).filter(Boolean)

                console.log(accessions)
                // console.log("accessions", accessions)
                // for (const acc of accessions) {
                //     console.log("dins del bucle")
                //     this.uploadedSpecies.push({acc, status:'ok'})
                // }
                this.uploadedSpecies.push({
                    assemblyAccession: assembly.accession,
                    assemblyName: assembly.assemblyName,
                    organismName: assembly.organismName,
                    accessions,
                    count: accessions.length
                })

                // this.$set(this.expandedSpecies, assembly.accession, false) 
                console.log(this.uploadedSpecies)
                this.$emit('genome-loaded', {
                    source: 'accession',
                    data: this.uploadedSpecies.flatMap(a => a.accessions)
                })
                this.showStatus(`${accessions.length} sequences loaded from ${assembly.assemblyName}`)
                this.activeTab = 'species'
            } catch (e) {
                this.showStatus(e.message, false)
            } finally {
                this.loadingSpecies = false
                this.closeSpeciesModal()  
            }

        },
        closeSpeciesModal() {
            this.showSpeciesModal  = false
            this.speciesAssemblies = []
            this.speciesSelected   = null
        },
        toggle(){
            if(!this.isRunning) {
                this.open = !this.open
            }
        },
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
        removeSpecies(index) {
            this.uploadedSpecies.splice(index, 1)
            this.$emit('genome-loaded', {
                source: 'accession',
                data: this.uploadedSpecies.flatMap(s => s.accessions)
            })
        },
        changeTabs(tabId){

            // if (this.activeTab !== tabId && this.uploadedAccessions.length > 0 || this.uploadedFiles.length > 0 || this.uploadedSpecies.length > 0){
            //     this.showStatus('Remove loaded accessions before using file upload mode.', false)
            //     return
            // }
            // this.activeTab = tabId
            let mes = 'genome'
            if (this.activeTab === 'accession'){
                mes = 'loaded accessions'
            } else if (this.activeTab === 'file') {
                mes = 'uploaded genome files'
            } else {
                mes = 'loaded species'
            }

            if( tabId === 'accession' && (this.uploadedFiles.length > 0 || this.uploadedSpecies.length > 0)){
                this.showStatus(`Remove ${mes} before using accession mode.`, false)
                return
            } else if (tabId === 'file' && (this.uploadedAccessions.length > 0 || this.uploadedSpecies.length > 0)){
                this.showStatus(`Remove ${mes} before using file upload mode.`, false)
                return
            } else if (tabId === 'species' && (this.uploadedAccessions.length> 0 || this.uploadedFiles.length > 0)){
                this.showStatus(`Remove ${mes} before using file upload mode`, false)
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
        },
        classifyGenomeError(e){
            if (e.message.includes("No records founds")) {
                return "No genome found for the provided accession number(s). Please check the accession(s) and try again."
            } else if (e.message.includes("Failed to fetch genome data")) {
                return "Network error while fetching genome data. Please check your connection and try again."
            } else if (e.message.includes("Unsupported file format")) {
                return "The uploaded file is not in a supported format. Please upload a valid GenBank file."
            } else {
                return e.message
            }
        }
    }, 
    computed: {
        isReady(){
            return this.pyodideStatus == 'ready'
        }, 
        isLoaded() {
            return this.uploadedFiles.length > 0 || this.uploadedAccessions.length > 0 || this.uploadedSpecies.length > 0;
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

.accession-sublist {
    margin: 0 0 6px 16px;
    padding: 6px 10px;
    border-left: 2px solid var(--color--border, #e2e8f0);
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.accession-subitem {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--color--text-secondary);
    padding: 2px 0;
}
</style>