const BASE =  "https://api.ncbi.nlm.nih.gov/datasets/v2"

export async function searchAssemblies(speciesName) {
    const encoded = encodeURIComponent(speciesName.trim())
    const params = new URLSearchParams({
        "filters.reference_only": "false",
        "filters.assembly_source": "refseq",
        "filters.exclude_atypical": "true",
       
    })

    const res = await fetch(`${BASE}/genome/taxon/${encoded}/dataset_report?${params}`, {headers: {Accept: "application/json"}})
    if (!res.ok){
        throw new Error(`NCBI error ${res.status}: ${await res.text()}`)
    }
    const data = await res.json()
    console.log(data.reports)

    let responses =  (data.reports ?? []).map(r => ({
        accession: r.accession ?? "",
        assemblyName: r.assembly_info?.assembly_name ?? "",
        assemblyLevel: r.assembly_info?.assembly_level ?? "",
        organismName: r.organism?.organism_name ?? "",
        taxId: r.organism?.tax_id ?? "",
        submitter: r.assembly_info?.submitter ?? "",
        releaseDate: r.assembly_info?.release_date?.split("T")[0] ?? "", 
        totalLength: r.assembly_stats?.total_sequence_length ?? 0,
        chromosomeCount: r.assembly_stats?.total_number_of_chromosomes ?? 0,
        refseqCategory: r.assembly_info?.refseq_category ?? "",

    }))

    console.log("Response", responses)
    return responses    
}

export async function getSequenceReports(assemblyAccession){
    const res = await fetch(
        `${BASE}/genome/accession/${assemblyAccession}/sequence_reports?role_filters=assembled-molecule`,
        { headers: { Accept: "application/json" } }
    )
    if (!res.ok) throw new Error(`NCBI error ${res.status}: ${await res.text()}`)

    const data = await res.json()

    console.log(data)

    return (data.reports ?? []).map(s => ({
        accession: s.refseq_accession ?? s.genbank_accession ?? "",
        chromosome: s.chr_name ?? "",
        length: s.length ?? 0,
        role: s.role ?? "",
    }))
}