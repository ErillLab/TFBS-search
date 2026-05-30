<script>


export default{
    name: "ResultsDownloader",
    props: {
        hits: {
            type: Array,
            required: true
        }
    },
    data() {
        return { open: true}
    },
    computed: {
        hasHits() {
            return this.hits && this.hits.length > 0;
        }, 
        fieldnames() {
            return [
                "Site ID",
                "Chromid Id",
                "Site Score",
                "Site Start",
                "Site End",
                "Site Strand",
                "Site Mode",
                "Relative Distance",
                "Gene locus tag",
                "Gene Name",
                "Protein Id",
                "Gene Start",
                "Gene End",
                "Gene Strand",
                "Gene Product",
                "Operon"
            ];
        }
    }, 
    methods: {
        convertToCSV() {
            const escapeCSV = (value, key) => {

            if (value === null || value === undefined) return "";

            /* ---------- CAS ESPECIAL OPERON ---------- */
            // if (key === "Operon") {

            //     // convertim a string estil Python
            //     let text;

            //     // if (Array.isArray(value) || typeof value === "object") {
            //     //     text = JSON.stringify(value)
            //     //         .replace(/"/g, "'"); // JSON → python-like
            //     // } else {
            //     //     text = String(value);
            //     // }

            //     // // Operon pot contenir comes → necessita quotes CSV
            //     // return `"${text}"`;
            //     if(Array.isArray(value) || typeof value === "object") {
            //         text = JSON.stringify(value).replace(/"/g, "'");
            //     } else {
            //         text = String(value)
            //     }
            //     return `"${text}"`;
            // }
            if (key === "Operon") {
                if (Array.isArray(value)) {
                    const text = value
                        .map(item => `${item.locus_tag}:${item.distance}`)
                        .join("|");
                    return `"${text}"`;
                }
                return `"${String(value)}"`;
            }


            /* ---------- RESTA DE CAMPS ---------- */

            if (Array.isArray(value)) {
                value = value.join(";");
            }

            value = String(value);
            value = value.replace(/;/g, "|");

            if (
                value.includes(",") ||
                value.includes('"') ||
                value.includes("\n") 
            ) {
                value = '"' + value.replace(/"/g, '""') + '"';
            }

            return value;
            };

            const header = this.fieldnames.join(",");
            const rows = this.hits.map(hit =>
                this.fieldnames
                    .map(key => escapeCSV(hit[key], key))
                    .join(",")
            );
            return header + "\n" + rows.join("\n");
        },

        downloadCSVFile() {
            const csv = this.convertToCSV();
            const blob = new Blob([csv], { type: "text/csv"});
            const url = URL.createObjectURL(blob)

            const a = document.createElement("a");
            a.href = url;
            a.download = "tfbs_results.csv";
            a.click();
            URL.revokeObjectURL(url);
        },
        downloadJSONFile() {
            const blob = new Blob([JSON.stringify(this.hits, null, 2)], {
                type: "application/json"
            });
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "tfbs_results.json";
            a.click();

            URL.revokeObjectURL(url);

        }
    }  
};
</script>

<template>
    <div class="panel-header" @click="open = !open">
        <div class="panel-header-left">
            <div class="panel-icon">
                <i class="ti ti-download" aria-hidden="true"></i>
            </div>
            <span class="panel-title">Results</span>
            <span v-if="hasHits" class="panel-badge ok">{{ hits.length }} hits</span>
        </div>
        <i class="ti ti-chevron-down chevron" :class="{open}" aria-hidden="true"></i>
    </div>

    <div v-show="open" class="panel-body">
        <div class="download-row">
            <button class="btn btn-download" :disabled="!hasHits" @click="downloadCSVFile">
                <i class="ti ti-file-type-csv" aria-hidden="true"></i>
                Download CSV
            </button>
             <button class="btn btn-download" :disabled="!hasHits" @click="downloadJSONFile">
                <i class="ti ti-file-type-js" aria-hidden="true"></i>
                Download JSON
            </button>
        </div>
    </div>
</template>


<style scoped>
.download-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn-download {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.25rem;
  background: var(--c-surface);
  color: var(--c-text);
  border: 1.5px solid var(--c-border);
  border-radius: 9px;
  font-size: 0.88rem;
  font-family: var(--font);
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s;
}
.btn-download:hover:not(:disabled) {
  border-color: var(--c-border-focus);
  background: var(--c-bg);
}
.btn-download:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn-download i { font-size: 17px; color: var(--c-muted); }
</style>