const loadPyodide = (await import(
  "https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.mjs"
)).loadPyodide;

let pyodide = null;
let cancelRequested = false;

let cancelView = null;

function writeFileChunked(path, content, chunkSize = 1024 * 1024) {
    try {pyodide.FS.unlink(path);} catch {}

    pyodide.FS.writeFile(path, new Uint8Array(0));

    for (let i = 0; i < content.length; i += chunkSize) {
        const chunk = content.slice(i, i+chunkSize);
        pyodide.FS.writeFile(path, chunk, {append: true});
    }
}

async function _loadTfbsModules(pyodide) {
    const tfbsModules = [
        'tfbs/__init__.py',
        'tfbs/cancel_flag.py',
        'tfbs/genome/__init__.py',
        'tfbs/genome/genome.py',
        'tfbs/genome/loader_genomes.py',
        'tfbs/motif/__init__.py',
        'tfbs/motif/motif.py',
        'tfbs/motif/loader_motifs.py',
        'tfbs/motif/threshold.py',
        'tfbs/scan/__init__.py',
        'tfbs/scan/scanner.py',
        'tfbs/scan/annotation.py',
        'tfbs/pipeline.py',
        'tfbs/update_pipeline.py'
    ]

    for (const modulePath of tfbsModules) {
        const response = await fetch(`${self.location.origin}/TFBS-search/python/${modulePath}`);
        if (!response.ok) {
            postMessage({
                type: "stderr",
                msg: `Error carregant mòdul Python: ${modulePath}`,
            });
            continue;
        }
        const code = await response.text()
        const path = `/home/pyodide/${modulePath}`
        const dir = path.substring(0, path.lastIndexOf('/'))
        pyodide.FS.mkdirTree(dir)
        pyodide.FS.writeFile(path, code)
    }
    await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, '/home/pyodide')
    `)
}


async function loadPyodideAndPackages() {
    try {
        pyodide = await loadPyodide({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.29.4/full/',
            stdout: (msg) => postMessage({type: "stdout", msg}),
            stderr: (msg) => postMessage({type: "stderr", msg}),
        });

        postMessage({type: "stdout", msg: "Pyodide loaded, loading micropip..."});
        await pyodide.loadPackage(['micropip']);

        postMessage({type: "stdout", msg: "Installing biopython..."});
        await pyodide.runPythonAsync(`import micropip
await micropip.install("biopython")
await micropip.install(
"https://ainaescobet.github.io/wa_entrez/wa_entrez-1.0.0-py3-none-any.whl"
            )
        `);

        postMessage({type: "stdout", msg: "Loading TFBS modules..."});
        await _loadTfbsModules(pyodide);  // <-- FIX: nom correcte amb _

        postMessage({type: "stdout", msg: "Setting up progress function..."});
        await pyodide.runPythonAsync(`
import js
def progress(msg):
    js.postMessage({"type": "progress", "msg": msg})
        `);

        postMessage({type: "ready"});
        postMessage({type: "stdout", msg: "Worker ready!"});
    } catch (err) {
        postMessage({
            type: "stderr",
            msg: "FATAL ERROR during init: " + err.toString() + "\n" + (err.stack || "")
        });
    }
}
loadPyodideAndPackages();

self.onmessage = async (event) => {
    console.log("[WORKER] Recived:", event.data)
    const { type, payload } = event.data;

    if(type === "init") {
        if(!event.data.supportsSAB) {
            cancelView = null;
        }
    }

    if (type === "init-cancel-buffer") {
        cancelView = new Uint8Array(event.data.buffer);
        return;
    }

  /* ---------------- VALIDACIÓ DE GENOMES ---------------- */
    if (type === "validate-genome") {
        const { filename, content } = payload;

        try {
            pyodide.FS.writeFile(`/tmp/${filename}`, content);
            // pyodide.FS.writeFileChunked(`/tmp/${filename}`, content);
            // writeFileChunked(`/tmp/${filename}`, content);


        await pyodide.runPythonAsync(`
from tfbs.genome.loader_genomes import load_from_file
load_from_file(["/tmp/${filename}"])
        `);

        postMessage({
            type: "genome-valid",
            payload: { ok: true },
        });

        } catch (err) {
        postMessage({
            type: "genome-valid",
            payload: { ok: false, error: err.toString() },
        });
        }
    }

  /* ---------------- VALIDACIÓ D’ACCESSIONS ---------------- */
    if (type === "validate-accession") {
        const { accession } = payload;

        try {
        const res = await pyodide.runPythonAsync(`
from tfbs.genome.loader_genomes import accession_exists
accession_exists("${accession}")
        `);
        console.log("[WORKER] Validating accession:", res);
        

        postMessage({
            type: "accession-valid",
            payload: { ok: true },
        });

        } catch (err) {
        console.error("[WORKER] ERROR in validate-accession:", err);
        postMessage({
            type: "accession-valid",
            payload: { ok: false, error: err.toString() },
        });
        }
    }

    if (type === "validate-motif-file") {
        const { filename, content } = payload;

        try {
            pyodide.FS.writeFile(`/tmp/${filename}`, content);

            await pyodide.runPythonAsync(`
from tfbs.motif.loader_motifs import load_motif
load_motif("/tmp/${filename}")
            `);

            postMessage({
            type: "motif-valid",
            payload: { ok: true },
            });

        } catch (err) {
            postMessage({
            type: "motif-valid",
            payload: { ok: false, error: err.toString() },
            });
        }
    }

    if (type === "validate-motif-text") {
        const { sequences } = payload;

        try {
            pyodide.FS.writeFile("/tmp/motif_from_text.txt", sequences.join("\n"));

            await pyodide.runPythonAsync(`
from tfbs.motif.motif import Motif
Motif.load_motif("/tmp/motif_from_text.txt")
            `);

            postMessage({
            type: "motif-text-valid",
            payload: { ok: true, path: "/tmp/motif_from_text.txt" },
            });

        } catch (err) {
            postMessage({
            type: "motif-text-valid",
            payload: { ok: false, error: err.toString() },
            });
        }
    }

  /* ---------------- EXECUCIÓ DEL PIPELINE ---------------- */
    
    if (type === "run") {
//         if(cancelView) Atomics.store(cancelView,0, 0);
//         cancelRequested = false;
//         const { code, files } = payload;

// //          await pyodide.runPythonAsync(`
// // from tfbs.cancel_flag import set_cancel_flag
// // set_cancel_flag(False) `);
//         pyodide.globals.set("_cancel_view", cancelView);
//         await pyodide.runPythonAsync(`
// from tfbs.cancel_flag import set_cancel_view
// set_cancel_view(_cancel_view)
//         `);
        const { code, files } = payload;
        if (cancelView !== null) {
            Atomics.store(cancelView, 0, 0);
            pyodide.globals.set("_cancel_view", cancelView);
            await pyodide.runPythonAsync(`
from tfbs.cancel_flag import set_cancel_view
set_cancel_view(_cancel_view)
from tfbs.cancel_flag import set_cancel_flag
set_cancel_flag(False)
            `);
        } else {
            await pyodide.runPythonAsync(`
from tfbs.cancel_flag import set_cancel_view
set_cancel_view(None)
from tfbs.cancel_flag import set_cancel_flag
set_cancel_flag(False)
            `);
        }
        

        try {
            if (files) {
                for (const f of files) {
                    pyodide.FS.writeFile(f.path, f.content);
                }
            }

            const result = await pyodide.runPythonAsync(code);
            // if (cancelRequested) {
            //     postMessage({type: "cancelled"});
            //     return;
            // }
            

            postMessage({
                type: "result",
                result,
            });

        } catch (err) {
            if (err.message?.includes("PipelineCancelledError")) {
                postMessage({ type: "cancelled" });
            } else {
                postMessage({ type: "error", error: err.toString() });
            }
        }
       
         
    }
    if( type === "cancel"){
//         console.log("CANELAAAAAAAAAAAAAAAT")
//         cancelRequested = true;
//         await pyodide.runPythonAsync(`
// from tfbs.scan. import set_cancel_flag
// set_cancel_flag(True)
//     `);
//         return;
        if(cancelView) {
            // Atomics.store(cancelView, 0, 1);
            cancelView[0] = 1;
        } else {
            pyodide.runPython(`
from tfbs.cancel_flag import set_cancel_flag
set_cancel_flag(True)
        `);
        }
    return;
    }
};