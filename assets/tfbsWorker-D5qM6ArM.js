(function(e){let t=null,n=!1;async function r(e){for(let t of[`tfbs/__init__.py`,`tfbs/cancel_flag.py`,`tfbs/genome/__init__.py`,`tfbs/genome/genome.py`,`tfbs/genome/loader_genomes.py`,`tfbs/motif/__init__.py`,`tfbs/motif/motif.py`,`tfbs/motif/loader_motifs.py`,`tfbs/motif/threshold.py`,`tfbs/scan/__init__.py`,`tfbs/scan/scanner.py`,`tfbs/scan/annotation.py`,`tfbs/pipeline.py`,`tfbs/update_pipeline.py`]){let n=await fetch(`${self.location.origin}/TFBS-search/python/${t}`);if(!n.ok){postMessage({type:`stderr`,msg:`Error carregant mòdul Python: ${t}`});continue}let r=await n.text(),i=`/home/pyodide/${t}`,a=i.substring(0,i.lastIndexOf(`/`));e.FS.mkdirTree(a),e.FS.writeFile(i,r)}await e.runPythonAsync(`
import sys
sys.path.insert(0, '/home/pyodide')
    `)}async function i(){try{t=await(0,e.loadPyodide)({indexURL:`https://cdn.jsdelivr.net/pyodide/v0.29.4/full/`,stdout:e=>postMessage({type:`stdout`,msg:e}),stderr:e=>postMessage({type:`stderr`,msg:e})}),postMessage({type:`stdout`,msg:`Pyodide loaded, loading micropip...`}),await t.loadPackage([`micropip`]),postMessage({type:`stdout`,msg:`Installing biopython...`}),await t.runPythonAsync(`import micropip
await micropip.install("biopython")
await micropip.install(
"https://ainaescobet.github.io/wa_entrez/wa_entrez-1.0.0-py3-none-any.whl"
            )
        `),postMessage({type:`stdout`,msg:`Loading TFBS modules...`}),await r(t),postMessage({type:`stdout`,msg:`Setting up progress function...`}),await t.runPythonAsync(`
import js
def progress(msg):
    js.postMessage({"type": "progress", "msg": msg})
        `),postMessage({type:`ready`}),postMessage({type:`stdout`,msg:`Worker ready!`})}catch(e){postMessage({type:`stderr`,msg:`FATAL ERROR during init: `+e.toString()+`
`+(e.stack||``)})}}i(),onmessage=async e=>{let{type:r,payload:i}=e.data;if(r===`validate-genome`){let{filename:e,content:n}=i;try{t.FS.writeFile(`/tmp/${e}`,n),await t.runPythonAsync(`
from tfbs.genome.loader_genomes import load_from_file
load_from_file(["/tmp/${e}"])
        `),postMessage({type:`genome-valid`,payload:{ok:!0}})}catch(e){postMessage({type:`genome-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-accession`){let{accession:e}=i;try{await t.runPythonAsync(`
from tfbs.genome.loader_genomes import load_from_accession
load_from_accession("${e}")
        `),postMessage({type:`accession-valid`,payload:{ok:!0}})}catch(e){postMessage({type:`accession-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-motif-file`){let{filename:e,content:n}=i;try{t.FS.writeFile(`/tmp/${e}`,n),await t.runPythonAsync(`
from tfbs.motif.loader_motifs import load_motif
load_motif("/tmp/${e}")
            `),postMessage({type:`motif-valid`,payload:{ok:!0}})}catch(e){postMessage({type:`motif-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`validate-motif-text`){let{sequences:e}=i;try{t.FS.writeFile(`/tmp/motif_from_text.txt`,e.join(`
`)),await t.runPythonAsync(`
from tfbs.motif.motif import Motif
Motif.load_motif("/tmp/motif_from_text.txt")
            `),postMessage({type:`motif-text-valid`,payload:{ok:!0,path:`/tmp/motif_from_text.txt`}})}catch(e){postMessage({type:`motif-text-valid`,payload:{ok:!1,error:e.toString()}})}}if(r===`cancel`){console.log(`CANELAAAAAAAAAAAAAAAT`),n=!0,await t.runPythonAsync(`
from tfbs.scan. import set_cancel_flag
set_cancel_flag(True)
    `);return}else if(r===`run`){n=!1;let{code:e,files:r}=i;await t.runPythonAsync(`
from tfbs.cancel_flag import set_cancel_flag
set_cancel_flag(False) `);try{if(r)for(let e of r)t.FS.writeFile(e.path,e.content);let i=await t.runPythonAsync(e);if(n){postMessage({type:`cancelled`});return}postMessage({type:`result`,result:i})}catch(e){e.message?.includes(`PipelineCancelledError`)?postMessage({type:`cancelled`}):postMessage({type:`error`,error:e.toString()})}}}})(https___cdn_jsdelivr_net_pyodide_v0_29_4_full_pyodide_mjs);