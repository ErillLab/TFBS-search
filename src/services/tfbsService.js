import { getPyodide } from "@/services/pyodide";

let pyodideInstance = null;

export async function getTfbsPyodide() {
  if (!pyodideInstance) {
    pyodideInstance = await getPyodide();
  }
  return pyodideInstance;
}

export function writeToVirtualFS(pyodide, filename, content){
    const path  = `/tmp/${filename}`
    if(Array.isArray(content)) {
        pyodide.FS.writeFile(path, content.join('\n'))
    } else if (typeof content === 'string'){
        pyodide.FS.writeFile(path, content)
    } else {
        pyodide.FS.writeFile(path, new Uint8Array(content))
    }
    return path
}

export async function readFileAsText(file){
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = e => resolve(e.target.result)
        reader.onerror = reject
        reader.readAsText(file)
    })
}

// export async function runTfbsPipeline({
//   genomeSource,
//   genomeData,
//   motifPath,
//   params,
// }) {
//   const pyodide = await getTfbsPyodide();
  

//   // Write files to virtual FS
// //   const genomePath = await writeToVirtualFS(pyodide, genomeFilename, genomeContent);
// //   const motifPath = await writeToVirtualFS(pyodide, motifFilename, motifContent);

//   // Convert params to JSON
//   const paramsJson = JSON.stringify(params);;

// let genomeArg;
// if (genomeSource === "file") {
//   const filesJson = JSON.stringify(Array.isArray(genomeData) ? genomeData : [genomeData]);
//   genomeArg = `genome_files=${filesJson}`;
// } else if (genomeSource === "accession") {
//   const accessionsJson = JSON.stringify(Array.isArray(genomeData) ? genomeData : [genomeData]);
//   genomeArg = `genome_accession=${accessionsJson}`;
// } else {
//   throw new Error("Genome Source desconegut");
// }
//   const resultJson = await pyodide.runPythonAsync(`
// import json

// from tfbs.update_pipeline import update_pipeline
// params = json.loads("""${paramsJson}""")

// res = update_pipeline(
//     ${genomeArg},
//     motif_file="${motifPath}",
//     params=params
// )

// json.dumps(res, default=str)
//   `);
//     console.log(resultJson)
//   // Convert Python JSON → JS object
//   return JSON.parse(resultJson);
// }
export function runTfbsPipeline({
  genomeSource,
  genomeData,
  motifPath,
  params,
}) {
  return getTfbsPyodide().then((pyodide) => {
    const paramsJson = JSON.stringify(params);

    let genomeArg;

    if (genomeSource === "file") {
      const filesJson = JSON.stringify(
        Array.isArray(genomeData) ? genomeData : [genomeData]
      );
      genomeArg = `genome_files=${filesJson}`;
    } else if (genomeSource === "accession") {
      const accessionsJson = JSON.stringify(
        Array.isArray(genomeData) ? genomeData : [genomeData]
      );
      genomeArg = `genome_accession=${accessionsJson}`;
    } else {
      throw new Error("Genome Source desconegut");
    }

    const pythonCode = `
import json
from tfbs.update_pipeline import update_pipeline

params = json.loads("""${paramsJson}""")

res = update_pipeline(
    ${genomeArg},
    motif_file="${motifPath}",
    params=params
)

json.dumps(res, default=str)
    `;

    return pyodide.runPythonAsync(pythonCode)
      .then((resultJson) => {
        console.log(resultJson);
        // return JSON.parse(resultJson);
        return {
          annotated: JSON.parse(resultJson).annotated,
          computedOperonDistance: JSON.parse(resultJson).computed_operon_distance,
        }
      });
  });
}