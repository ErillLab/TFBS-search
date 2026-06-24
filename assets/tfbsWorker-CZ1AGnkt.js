(function(){importScripts(`https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.js`);let e=null,t=null;async function n(e){for(let t of[`tfbs/__init__.py`,`tfbs/cancel_flag.py`,`tfbs/genome/__init__.py`,`tfbs/genome/genome.py`,`tfbs/genome/loader_genomes.py`,`tfbs/motif/__init__.py`,`tfbs/motif/motif.py`,`tfbs/motif/loader_motifs.py`,`tfbs/motif/threshold.py`,`tfbs/scan/__init__.py`,`tfbs/scan/scanner.py`,`tfbs/scan/annotation.py`,`tfbs/pipeline.py`,`tfbs/update_pipeline.py`]){let n=await fetch(`${self.location.origin}/TFBS-search/python/${t}`);if(!n.ok){postMessage({type:`stderr`,msg:`Error carregant mòdul Python: ${t}`});continue}let r=await n.text(),i=`/home/pyodide/${t}`,a=i.substring(0,i.lastIndexOf(`/`));e.FS.mkdirTree(a),e.FS.writeFile(i,r)}await e.runPythonAsync(`
import sys
sys.path.insert(0, '/home/pyodide')
    `)}async function r(){try{e=await loadPyodide({indexURL:`https://cdn.jsdelivr.net/pyodide/v0.29.4/full/`,stdout:e=>postMessage({type:`stdout`,msg:e}),stderr:e=>postMessage({type:`stderr`,msg:e})}),postMessage({type:`stdout`,msg:`Pyodide loaded, loading micropip...`}),await e.loadPackage([`micropip`]),postMessage({type:`stdout`,msg:`Installing biopython...`}),await e.runPythonAsync(`import micropip
await micropip.install("biopython")
await micropip.install(
"https://ainaescobet.github.io/wa_entrez/wa_entrez-1.0.0-py3-none-any.whl"
            )
        `),postMessage({type:`stdout`,msg:`Loading TFBS modules...`}),await n(e),postMessage({type:`stdout`,msg:`Setting up progress function...`}),await e.runPythonAsync(`
import js
def progress(msg):
    js.postMessage({"type": "progress", "msg": msg})
        `),postMessage({type:`ready`}),postMessage({type:`stdout`,msg:`Worker ready!`})}catch(e){postMessage({type:`stderr`,msg:`FATAL ERROR during init: `+e.toString()+`
`+(e.stack||``)})}}r(),onmessage=async n=>{console.log(`[WORKER] Recived:`,n.data);let{type:r,payload:i}=n.data;if(r===`init-cancel-buffer`){t=new Uint8Array(n.data.buffer);return}if(r===`validate-genome`){let{filename:t,content:n}=i;try{e.FS.writeFile(`/tmp/${t}`,n),await e.runPythonAsync(`
from tfbs.genome.loader_genomes import load_from_file
load_from_file(["/tmp/${t}"])
        `),postMessage({type:`genome-valid`,payload:{ok:!0}})}catch(e){postMessage({type:`genome-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-accession`){let{accession:t}=i;try{let n=await e.runPythonAsync(`
from tfbs.genome.loader_genomes import accession_exists
accession_exists("${t}")
        `);console.log(`[WORKER] Validating accession:`,n),postMessage({type:`accession-valid`,payload:{ok:!0}})}catch(e){console.error(`[WORKER] ERROR in validate-accession:`,e),postMessage({type:`accession-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-motif-file`){let{filename:t,content:n}=i;try{e.FS.writeFile(`/tmp/${t}`,n),await e.runPythonAsync(`
from tfbs.motif.loader_motifs import load_motif
load_motif("/tmp/${t}")
            `),postMessage({type:`motif-valid`,payload:{ok:!0}})}catch(e){postMessage({type:`motif-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-motif-text`){let{sequences:t}=i;try{e.FS.writeFile(`/tmp/motif_from_text.txt`,t.join(`
`)),await e.runPythonAsync(`
from tfbs.motif.motif import Motif
Motif.load_motif("/tmp/motif_from_text.txt")
            `),postMessage({type:`motif-text-valid`,payload:{ok:!0,path:`/tmp/motif_from_text.txt`}})}catch(e){postMessage({type:`motif-text-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`run`){let{code:n,files:r}=i;t===null?await e.runPythonAsync(`
from tfbs.cancel_flag import set_cancel_view
set_cancel_view(None)
            `):(Atomics.store(t,0,0),e.globals.set(`_cancel_view`,t),await e.runPythonAsync(`
from tfbs.cancel_flag import set_cancel_view
set_cancel_view(_cancel_view)
            `));try{if(r)for(let t of r)e.FS.writeFile(t.path,t.content);let t=await e.runPythonAsync(n);postMessage({type:`result`,result:t})}catch(e){e.message?.includes(`PipelineCancelledError`)?postMessage({type:`cancelled`}):postMessage({type:`error`,error:e.toString()})}}r===`cancel`&&(t?Atomics.store(t,0,1):e.runPython(`
from tfbs.cancel_flag import set_cancel_flag
set_cancel_flag(True)
        `))}})();