const e=(await import(`https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.mjs`)).loadPyodide;let t=null,n=null;async function r(e){for(let t of[`tfbs/__init__.py`,`tfbs/cancel_flag.py`,`tfbs/genome/__init__.py`,`tfbs/genome/genome.py`,`tfbs/genome/loader_genomes.py`,`tfbs/motif/__init__.py`,`tfbs/motif/motif.py`,`tfbs/motif/loader_motifs.py`,`tfbs/motif/threshold.py`,`tfbs/scan/__init__.py`,`tfbs/scan/scanner.py`,`tfbs/scan/annotation.py`,`tfbs/pipeline.py`,`tfbs/update_pipeline.py`]){let n=await fetch(`${self.location.origin}/TFBS-search/python/${t}`);if(!n.ok){postMessage({type:`stderr`,msg:`Error carregant mòdul Python: ${t}`});continue}let r=await n.text(),i=`/home/pyodide/${t}`,a=i.substring(0,i.lastIndexOf(`/`));e.FS.mkdirTree(a),e.FS.writeFile(i,r)}await e.runPythonAsync(`
import sys
sys.path.insert(0, '/home/pyodide')
    `)}async function i(){try{t=await e({indexURL:`https://cdn.jsdelivr.net/pyodide/v0.29.4/full/`,stdout:e=>postMessage({type:`stdout`,msg:e}),stderr:e=>postMessage({type:`stderr`,msg:e})}),postMessage({type:`stdout`,msg:`Pyodide loaded, loading micropip...`}),await t.loadPackage([`micropip`]),postMessage({type:`stdout`,msg:`Installing biopython...`}),await t.runPythonAsync(`import micropip
await micropip.install("biopython")
await micropip.install(
"https://ainaescobet.github.io/wa_entrez/wa_entrez-1.0.0-py3-none-any.whl"
            )
        `),postMessage({type:`stdout`,msg:`Loading TFBS modules...`}),await r(t),postMessage({type:`stdout`,msg:`Setting up progress function...`}),await t.runPythonAsync(`
import js
def progress(msg):
    js.postMessage({"type": "progress", "msg": msg})
        `),postMessage({type:`ready`}),postMessage({type:`stdout`,msg:`Worker ready!`})}catch(e){postMessage({type:`stderr`,msg:`FATAL ERROR during init: `+e.toString()+`
`+(e.stack||``)})}}i(),onmessage=async e=>{console.log(`[WORKER] Recived:`,e.data);let{type:r,payload:i}=e.data;if(r===`init-cancel-buffer`){n=new Uint8Array(e.data.buffer);return}if(r===`validate-genome`){let{filename:e,content:n}=i;try{t.FS.writeFile(`/tmp/${e}`,n),await t.runPythonAsync(`
from tfbs.genome.loader_genomes import load_from_file
load_from_file(["/tmp/${e}"])
        `),postMessage({type:`genome-valid`,payload:{ok:!0}})}catch(e){postMessage({type:`genome-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-accession`){let{accession:e}=i;try{let n=await t.runPythonAsync(`
from tfbs.genome.loader_genomes import accession_exists
accession_exists("${e}")
        `);console.log(`[WORKER] Validating accession:`,n),postMessage({type:`accession-valid`,payload:{ok:!0}})}catch(e){console.error(`[WORKER] ERROR in validate-accession:`,e),postMessage({type:`accession-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-motif-file`){let{filename:e,content:n}=i;try{t.FS.writeFile(`/tmp/${e}`,n),await t.runPythonAsync(`
from tfbs.motif.loader_motifs import load_motif
load_motif("/tmp/${e}")
            `),postMessage({type:`motif-valid`,payload:{ok:!0}})}catch(e){postMessage({type:`motif-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-motif-text`){let{sequences:e}=i;try{t.FS.writeFile(`/tmp/motif_from_text.txt`,e.join(`
`)),await t.runPythonAsync(`
from tfbs.motif.motif import Motif
Motif.load_motif("/tmp/motif_from_text.txt")
            `),postMessage({type:`motif-text-valid`,payload:{ok:!0,path:`/tmp/motif_from_text.txt`}})}catch(e){postMessage({type:`motif-text-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`run`){n&&Atomics.store(n,0,0);let{code:e,files:r}=i;t.globals.set(`_cancel_view`,n),await t.runPythonAsync(`
from tfbs.cancel_flag import set_cancel_view
set_cancel_view(_cancel_view)
        `);try{if(r)for(let e of r)t.FS.writeFile(e.path,e.content);let n=await t.runPythonAsync(e);postMessage({type:`result`,result:n})}catch(e){e.message?.includes(`PipelineCancelledError`)?postMessage({type:`cancelled`}):postMessage({type:`error`,error:e.toString()})}}r===`cancel`&&n&&Atomics.store(n,0,1)};