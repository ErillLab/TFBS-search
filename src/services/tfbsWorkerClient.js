// // src/services/tfbsWorkerClient.js
// import { getTfbsWorker, getTfbsWorkerReady } from "./tfbsWorkerInstance";

// export async function runTfbsPipelineInWorker({
//     genomeSource,
//     genomeData,
//     motifPath,
//     params,
//     onProgress,
//     onStdout,
//     onStderr
// }) {
//     const w = getTfbsWorker();
//     await getTfbsWorkerReady();

//     const files = [];
//     let genomeArg;

//     if (genomeSource === "file") {
//         const genomeText = Array.isArray(genomeData) ? genomeData.join("\n") : genomeData;
//         files.push({ path: "/tmp/genome.gb", content: genomeText });
//         genomeArg = `genome_files=["/tmp/genome.gb"]`;
//     } else {
//         const acc = JSON.stringify(Array.isArray(genomeData) ? genomeData : [genomeData]);
//         genomeArg = `genome_accession=${acc}`;
//     }
//     // files.push({ path: "/tmp/motif.txt", content: motifContent });

//     const paramsJson = JSON.stringify(params);

//     const code = `
// import json

// from tfbs.update_pipeline import update_pipeline
// params = json.loads("""${paramsJson}""")

// res = update_pipeline(
//     ${genomeArg},
//     motif_file=${motifPath},
//     params=params
// )

// json.dumps(res, default=str)`;

//     return new Promise((res, reject) => {
//         const handler = (e) => {
//             const { type, msg, result, error } = e.data;

//             // Events de progrés/log: no resolen la promesa, simplement informen
//             if (type === "progress" && onProgress) {
//                 onProgress(msg);
//                 return;
//             }
//             if (type === "stdout" && onStdout) {
//                 onStdout(msg);
//                 return;
//             }
//             if (type === "stderr" && onStderr) {
//                 onStderr(msg);
//                 return;
//             }

//             if (type === "result") {
//                 w.removeEventListener("message", handler);
//                 res(JSON.parse(result));
//             } else if (type === "error") {
//                 w.removeEventListener("message", handler);
//                 reject(error);
//             }
//         };

//         w.addEventListener("message", handler);
//         w.postMessage({
//             type: "run",
//             payload: { code, files },
//         });
//     });
// }

// src/services/tfbsWorkerClient.js
import { getTfbsWorker, getTfbsWorkerReady } from "./tfbsWorkerInstance";

export async function runTfbsPipelineInWorker({
    genomeSource,
    genomeData,
    motifPath,
    params,
    onProgress,
    onStdout,
    onStderr,
}) {
    const w = getTfbsWorker();
    await getTfbsWorkerReady();

    const files = [];
    let genomeArg;

    if (genomeSource === "file") {
        const genomeText = Array.isArray(genomeData) ? genomeData.join("\n") : genomeData;
        files.push({ path: "/tmp/genome.gb", content: genomeText });
        genomeArg = `genome_files=["/tmp/genome.gb"]`;
    } else {
        const acc = JSON.stringify(Array.isArray(genomeData) ? genomeData : [genomeData]);
        genomeArg = `genome_accession=${acc}`;
    }

    const paramsJson = JSON.stringify(params);

    const code = `
import json

from tfbs.update_pipeline import update_pipeline
params = json.loads("""${paramsJson}""")

res = update_pipeline(
    ${genomeArg},
    motif_file="${motifPath}",
    params=params
)

json.dumps(res, default=str)`;

    return new Promise((res, reject) => {
        const handler = (e) => {
            const { type, msg, result, error } = e.data;

            if (type === "progress" && onProgress) { onProgress(msg); return; }
            if (type === "stdout" && onStdout) { onStdout(msg); return; }
            if (type === "stderr" && onStderr) { onStderr(msg); return; }

            if (type === "result") {
                w.removeEventListener("message", handler);
                // res(JSON.parse(result));
                const parsed = JSON.parse(result);

                res({
                    annotated: parsed.annotated,
                    computedOperonDistance: parsed.computed_operon_distance,  // <--- aquí!
                    metadata: parsed.metadata ?? null
                });
            } else if (type === "cancelled"){
                w.removeEventListener("message", handler);
                reject(new Error("Pipeline cancelled by user."))

            } else if (type === "error") {
                w.removeEventListener("message", handler);
                reject(new Error(error));
            } 
        };

        w.addEventListener("message", handler);
        w.postMessage({
            type: "run",
            payload: { code, files },
        });
    });
}


export function cancelTfbsPipeline() {
    const w = getTfbsWorker()
    w.postMessage({type: "cancel"});
}