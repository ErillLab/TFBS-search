<template>
  <div style="font-family: monospace; padding: 1rem;">
    <h2>Test Pyodide + tfbs</h2>

    <div v-if="status === 'idle'">
      <button @click="runTest">Iniciar càrrega i test</button>
    </div>

    <div v-if="status === 'loading'">
      {{ currentStep }}
    </div>

    <div v-if="status === 'ok'" style="color: green">
      Tot funciona correctament
      <pre>{{ output }}</pre>
    </div>

    <div v-if="status === 'error'" style="color: red">
      Error: {{ errorMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getPyodide } from '@/services/pyodide'

const status = ref('idle')
const currentStep = ref('')
const output = ref('')
const errorMsg = ref('')

async function runTest() {
  status.value = 'loading'
  try {
    currentStep.value = 'Carregant Pyodide i biopython...'
    const pyodide = await getPyodide()

    currentStep.value = 'Executant test dels mòduls tfbs...'
    const result = await pyodide.runPythonAsync(`
from tfbs.motif.motif import Motif
from tfbs.motif.loader_motifs import from_list_of_sequences
from tfbs.scan.scanner import scan_sequence
from tfbs.genome.genome import Genome
 
# Test 1: crear un motiu
seqs = ["ACGTACGT", "ACGTACGT", "TTGTACGT"]
motif = Motif.from_list_of_sequences(seqs)
sequence = "ACGTACGT"
genome = Genome.from_accession("NZ_JBQPCT010000034.1")
print("genome:")
print(genome)
print(genome.chromids)
# Test 2: generar PSSM
pssm = motif.pssm
print(motif.pssm)
scores = pssm.calculate(sequence)
print(scores) 
print(type(scores))
# Test 4: escanejar una seqüència
hits = scan_sequence("ACGTACGT",motif, threshold=10)

f"motiu longitud={motif.length} |  | hits={len(hits)}"
    `)

    output.value = result
    status.value = 'ok'

  } catch (e) {
    errorMsg.value = e.message || String(e)
    status.value = 'error'
  }
}
</script>