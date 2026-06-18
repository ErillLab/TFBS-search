

<template>
  <div class="panel results-panel">

    <div class="panel-header" @click="toggleOpen">
      <div class="panel-header-left">
        <div class="panel-icon">
          <i class="ti ti-table" aria-hidden="true"></i>
        </div>
        <span class="panel-title">Results table</span>
        <span v-if="hits?.length" class="panel-badge ok">{{ hits.length }} results</span>
      </div>
      <i class="ti ti-chevron-down chevron" :class="{ open }" aria-hidden="true"></i>
    </div>

    <div v-show="open" class="panel-body results-body">
      <div ref="grid" class="grid-wrapper"></div>
    </div>

  </div>
</template>

<script>
import { Grid } from 'gridjs'
import 'gridjs/dist/theme/mermaid.min.css'

export default {
  name: 'ResultsTable',
  props: {
    hits: { type: Array, required: true }
  },
  data() {
    return { open: false }
  },
  watch: {
    hits: {
        immediate: true,
        handler() {
            this.$nextTick(() => {this.renderGrid()})
        }
    }
  },
  methods: {
    renderGrid() {

        if (!this.hits?.length) return

        if (this.grid) {
        this.grid.destroy()
        this.grid = null
        }

        const columns = [
        "Site ID", "Chromid Id", "Site Score", "Site Start", "Site End",
        "Site Strand", "Site Mode", "Relative Distance", "Gene locus tag",
        "Gene Name", "Protein Id", "Gene Start", "Gene End",
        "Gene Strand", "Gene Product", "Operon"
        ]

        const numericCols = new Set([
        "Site ID", "Site Score", "Site Start", "Site End",
        "Relative Distance", "Gene Start", "Gene End", "Gene Strand"
        ])

        const formatOperon = op => {
        if (!op) return ""

        if (Array.isArray(op)) {
           return op
            
            .map(g => `${g.locus_tag} (${g.distance})`)
            .join(" | ")

        }

        return String(op)
        }

        const rows = this.hits.map(hit =>
        columns.map(col => {

            let v = hit[col]

            if (col === "Operon") {
            v = formatOperon(v)
            }

            if (numericCols.has(col)) {
            return Number(v)
            }

            return v ?? ""
        })
        )

        this.grid = new Grid({
        columns,
        data: rows,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        resizable: true,

        className: {
            container: 'tfbs-grid-container',
            table: 'tfbs-grid-table',
            thead: 'tfbs-grid-thead',
            th: 'tfbs-grid-th',
            td: 'tfbs-grid-td',
            search: 'tfbs-grid-search',
            paginationButton: 'tfbs-grid-page-btn',
            paginationButtonCurrent: 'tfbs-grid-page-btn current',
            
        }
        })

        this.grid.render(this.$refs.grid)
    },
    toggleOpen() {
      this.open = !this.open
      if (this.open) {
        this.$nextTick(() => {
          this.$el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        })
      }
    }
  }
}
</script>

<style scoped>
.results-body { padding: 1.25rem; }

.grid-wrapper { width: 100%; overflow-x: auto; }
</style>

<style>
.tfbs-grid-container {
  font-family: var(--font) !important;
  font-size: 0.82rem !important;
  border: none !important;
}

.tfbs-grid-table {
  /* width: 100% !important; */
  width: max-content !important;
  min-width: 100% !important;
  border-collapse: collapse !important;
  border: none !important;
}

.tfbs-grid-thead tr {
  background: var(--c-bg) !important;
  border-bottom: 1.5px solid var(--c-border) !important;
}

.tfbs-grid-th,
.tfbs-grid-td {
  text-align: center;
  vertical-align: middle;}

.tfbs-grid-th {
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  color: var(--c-muted) !important;
  padding: 0.65rem 0.75rem !important;
  background: var(--c-bg) !important;
  border: none !important;
  white-space: nowrap !important;
  text-align: center !important;

}

.tfbs-grid-td {
  padding: 0.6rem 0.75rem !important;
  border: none !important;
  border-bottom: 1px solid var(--c-border) !important;
  color: var(--c-text) !important;
  font-family: var(--mono) !important;
  font-size: 0.78rem !important;
  white-space: nowrap !important;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center !important;
}

tr:hover .tfbs-grid-td {
  background: var(--c-bg) !important;
}

/* Search input */
.gridjs-search input {
  font-family: var(--font) !important;
  font-size: 0.85rem !important;
  padding: 0.5rem 0.9rem !important;
  border: 1.5px solid var(--c-border) !important;
  border-radius: 9px !important;
  outline: none !important;
  margin-bottom: 1rem !important;
  width: 100% !important;
  max-width: 320px !important;
  background: var(--c-surface) !important;
  color: var(--c-text) !important;
}
.gridjs-search input:focus {
  border-color: var(--c-border-focus) !important;
}

/* Pagination */
.gridjs-pagination {
  padding-top: 0.75rem !important;
  border-top: 1px solid var(--c-border) !important;
  margin-top: 0.25rem !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 0.25rem !important;
  font-family: var(--font) !important;
}

.tfbs-grid-page-btn {
  padding: 0.3rem 0.65rem !important;
  border: 1px solid var(--c-border) !important;
  border-radius: 7px !important;
  background: none !important;
  font-size: 0.78rem !important;
  font-family: var(--font) !important;
  color: var(--c-muted) !important;
  cursor: pointer !important;
  transition: border-color 0.15s, color 0.15s !important;
}
.tfbs-grid-page-btn:hover {
  border-color: var(--c-border-focus) !important;
  color: var(--c-text) !important;
}
.tfbs-grid-page-btn.current {
  background: var(--c-text) !important;
  color: white !important;
  border-color: var(--c-text) !important;
}
</style>