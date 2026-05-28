<script>
import { getPyodide } from '@/services/pyodide';

export default{
    name: "PyodideUploader",
    data(){
        return{
            // Pyodide state
            pyodideStatus: 'loading',
            pyodideError: '',
            pyodide: null,

            // Results
            genomeResult: null,
            motifResult: null, 

            //Inputs
            accessionInput: '',
            motifText: ''
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
        readFileAsText(file){
            return new Promise((resolve, reject) => {
                const reader = new FileReader()
                reader.onload = e => resolve(e.target.result)
                reader.onerror = reject
                reader.readAsText(file)
            })
        }, 
        writeToVirtualFS(filename, content){
            const path  = `/tmp/${filename}`
            if (typeof content === 'string'){
                this.pyodide.FS.writeFile(path, content)
            } else {
                this.pyodide.FS.writeFile(path, new Uint8Array(content))
            }
            return path
        },
        // Genome file
        async onGenomeFile(event){
            this.genomeResult = null
            if(!this.isReady) return
            const file = event.target.files[0]
            if (!file) return
            try{
                const content = await this.readFileAsText(file)
                const path = this.writeToVirtualFS(file.name, content)

                const result = await this.pyodide.runPythonAsync(`
                from tfbs.genome.loader_genomes import load_from_file
                records = load_from_file(["${path}"])
                f"OK - {len(records)} chromids: {[r.id for r in records]}"

                `)
                this.genomeResult = {ok: true, msg: result}
            }
            catch(e){
                this.genomeResult = {ok: false, msg: e.message}
            }
        }, 
        //Accession
        async Accessions(){
            this.genomeResult = null
            if (!this.isReady || !this.accessionInput.trim()) return

            const accessions = this.accessionInput
                .split(',')
                .map(a => a.trim())
                .filter(Boolean)

            try {

                const accJson = JSON.stringify(accessions)
                
                const result = await this.pyodide.runPythonAsync(`
                import json
                from tfbs.genome.loader_genomes import load_genome
                accessions = json.loads('${accJson}')
               
                records = load_genome(accessions)
                f"OK — {accessions} {len(records)} chromid(s): {[r.id for r in records]} "
                `)

                this.genomeResult = { ok: true, msg: result }

            } catch (e) {
                this.genomeResult = { ok: false, msg: e.message }
            }
        }, 
        async onMotifFile(event, format) {

            this.motifResult = null
            if (!this.isReady) return

            const file = event.target.files[0]
            if (!file) return

            try {

                const content = await this.readFileAsText(file)
                const path = this.writeToVirtualFS(file.name, content)

                const result = await this.pyodide.runPythonAsync(`
                from tfbs.motif.loader_motifs import load_motif
                motif = load_motif("${path}")
                f"OK — motiu longitud={motif.length}, format=${format}" 
                `)

                this.motifResult = { ok: true, msg: result }

            } catch (e) {
                this.motifResult = { ok: false, msg: e.message }
            }
        },

        async testMotifText() {

            this.motifResult = null
            if (!this.isReady || !this.motifText.trim()) return

            try {

                const sequences = this.motifText
                .split('\n')
                .map(s => s.trim().toUpperCase())
                .filter(Boolean)

                const seqJson = JSON.stringify(sequences)
                print(seqJson)

                const result = await this.pyodide.runPythonAsync(`
                    import json
                    from tfbs.motif.loader_motifs import load_motif
                    seqs = json.loads('${seqJson}')
                    f"{seqs}"
                    motif = load_motif(seqs)
                    f"OK — motiu longitud={motif.length}, {len(seqs)} seqüències"
                `)

                this.motifResult = { ok: true, msg: result }

            } catch (e) {
                this.motifResult = { ok: false, msg: e.message }
            }
        }
  
    },
    computed: {
        isReady() {
            return this.pyodideStatus == 'ready'
        }
    }
}

</script>

<template>
    <div style="font-family: monospace; padding: 1rem; max-width: 800px;">
        <h2>Test pujada de fitxers cap a Pyodide</h2>

        <div v-if="pyodideStatus === 'loading'" style="color: orangered;">
            Charging Pyodide...
        </div>
        <div v-else-if="pyodideStatus === 'ready'" style="color: green">
            Pyodide ready
        </div>
        <div v-else-if="pyodideStatus === 'error'" style="color: red;">
            Error with Pyodide: {{ pyodideError }}
        </div>

        <hr />
        <section>
            <h3>Genome</h3>
            <div>
                <label> Genbank File (.gb, .gbk, .gbff):</label> <br />
                <input
                type="file"
                accept=".gb,.gbk,.genbank,.gbff"
                @change="onGenomeFile"
                />
            </div>

            <br />

            <div>
                <label> Accession number (NCBI):</label><br />
                <input
                v-model="accessionInput"
                type="text"
                placeholder="ex:  NC_000913.3 o NC_000913,NC_000914"
                style="width: 400px;"
                />
                <button @click="Accessions" :disabled="!isReady">
                    Test accession (Entrez)
                </button>
                
            </div>
            <pre v-if="genomeResult" :style="{color:genomeResult.ok ? 'green' : 'red'}">
                {{ genomeResult.msg }}
            </pre>
        </section>
    </div>

     <section>
      <h3>Motif</h3>

      <!-- FASTA file -->
      <div>
        <label>Fitxer FASTA (.fasta, .fa):</label><br />
        <input type="file" accept=".fasta,.fa" @change="e => onMotifFile(e, 'fasta')" />
      </div>

      <br />

      <!-- TXT file -->
      <div>
        <label>Fitxer TXT (.txt):</label><br />
        <input type="file" accept=".txt" @change="e => onMotifFile(e, 'txt')" />
      </div>

      <br />

      <!-- Text box (còpia manual) -->
      <div>
        <label>O enganxa seqüències directament (una per línia):</label><br />
        <textarea id="text_motif"
          v-model="motifText"
          rows="5"
          cols="50"
          placeholder="ACGTACGT&#10;TTGTACGT&#10;ACGTACGT" ></textarea> <br />
        <div><button type="button"
        @click="testMotifText" :disabled="!isReady">
          Provar text
        </button></div>
        
      </div>

      <!-- JASPAR file -->
      <br />
      <div>
        <label>Fitxer JASPAR (.jaspar):</label><br />
        <input type="file" accept=".jaspar" @change="e => onMotifFile(e, 'jaspar')" />
      </div>

      <pre v-if="motifResult" :style="{ color: motifResult.ok ? 'green' : 'red' }">
{{ motifResult.msg }}</pre>
    </section>




</template>