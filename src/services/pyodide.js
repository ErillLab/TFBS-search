// import { C } from "vue-router/dist/options-C8M2qFcl.cjs"

let pyodideInstance = null
let pyodideLoadingPromise = null

export async function getPyodide() {
    if (pyodideInstance) return pyodideInstance
    if (pyodideLoadingPromise) return pyodideLoadingPromise

    pyodideLoadingPromise = _loadPyodide()
    pyodideInstance = await pyodideLoadingPromise
    return pyodideInstance
}

async function _loadTfbsModules(pyodide) {
    const tfbsModules = [
        'tfbs/__init__.py',
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
        const response = await fetch(`${import.meta.env.BASE_URL}python/${modulePath}`)
        if (!response.ok) {
            throw new Error(`Failed to load module: ${modulePath}`)
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

async function _loadPyodide() {
    const { loadPyodide } = await import('pyodide')

    const pyodide = await loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.29.4/full/',
    })
    await pyodide.loadPackage(['micropip'])
    await pyodide.runPythonAsync(`
        import micropip
        await micropip.install("biopython")
        await micropip.install(
        "https://ainaescobet.github.io/wa_entrez/wa_entrez-1.0.0-py3-none-any.whl"
        )
        `)

    await _loadTfbsModules(pyodide)
    // await pyodide.runPythonAsync(`
    //     from tfbs.genome.genome import Genome
    //     from tfbs.motif.motif import Motif
    //     from tfbs.scan.scanner import scan_sequence 
    // `)
    return pyodide
}

export function isPyodideLoaded() {
    return pyodideInstance !== null
}