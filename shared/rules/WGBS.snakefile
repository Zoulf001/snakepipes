###get automatic cut threshold for hard-trimming of 5' ends

if trimReads=='auto':
    if fqcin:
        rule get_cut_thd:
            input:
                R1zip = fqcin+"/{sample}"+reads[0]+"_fastqc.zip",
                R2zip = fqcin+"/{sample}"+reads[1]+"_fastqc.zip"
            output:
                R12ct= "fastqc_cut/{sample}"+".R12.ct.txt"
            log:"fastqc_cut/logs/{sample}.cutThd.log"
            run:####import function or sth

    rule trimReads:
        input:
            R1 = "FASTQ/{sample}"+reads[0]+".fastq.gz",
            R2 = "FASTQ/{sample}"+reads[1]+".fastq.gz",
            R12ct= "fastqc_cut/{sample}"+".R12.ct.txt"
        output:
            R1cut="FASTQ_Cutadapt/{sample}"+reads[0]+".fastq.gz",
            R2cut="FASTQ_Cutadapt/{sample}"+reads[1]+".fastq.gz"
        params:
            nthreads=8
            cutThdR1=
            cutThdR2=
        log:"FASTQ_Cutadapt/logs/{sample}.log"
        shell:cutpath +' cutadapt -a AGATCGGAAGAGC -A AGATCGGAAGAGC --minimum-length 30  -n 5 -j' + {params.nthreads} +' -u ' + {params.cutThdR1} + ' -U ' + {params.cutThdR2} + ' -o ' + {output.R1cut} + ' -p ' + {output.R2cut} + ' ' + {input.R1} + ' ' + {input.R2}

elif trimReads=='user':
    rule trimReads:
        input:
            R1 = "FASTQ/{sample}"+reads[0]+".fastq.gz",
            R2 = "FASTQ/{sample}"+reads[1]+".fastq.gz"
        output:
            R1out="FASTQ_Cutadapt/{sample}"+reads[0]+".fastq.gz",
            R2out="FASTQ_Cutadapt/{sample}"+reads[1]+".fastq.gz"
        params:
            nthreads=8
            adapterSeq=adapterDict[adapterMode]
            trimThreshold=trimThreshold
            trimOtherArgs=trimOtherArgs
        log:
        shell:"{} cutadapt -a {} -A {} -q {} -m 30 -j {} {} -o {} -p {} {} {} ".format(cutpath,
                                                                            {params.adapterSeq},
                                                                            {params.adapterSeq},
                                                                            {params.trimThreshold},
                                                                            {params.nthreads},
                                                                            {params.trimOtherArgs},
                                                                            {output.R1out},
                                                                            {output.R2out},
                                                                            {input.R1},
                                                                            {input.R2})

if not trimReads is None:
    rule postTrimFastQC:
        input:
            R1cut="FASTQ_Cutadapt/{sample}"+reads[0]+".fastq.gz",
            R2cut="FASTQ_Cutadapt/{sample}"+reads[1]+".fastq.gz"
        output:
            R1fqc="FASTQC_Cut/{sample}"+reads[0]+".fastqc.html",
            R2fqc="FASTQC_Cut/{sample}"+reads[1]+".fastqc.html"
        log:"FASTQC_Cut/logs/{sample}.log"
        shell:os.path.join(FQCpath,'fastqc ')+' --outdir ' + fqcout + ' -t 8 '+ {input.R1cut} + ' ' + {input.R2cut}###finish editing

if convRef:
    rule conv_ref:
        input:refG
        output:aux_files/###
        log:
        shell:

if convRef and not trimReads is None:
    rule map_reads:
        input:
            R1cut
            R2cut
            crefG
        output:
        params:
            nthreads=8
        log:
        shell:

if convRef and trimReads is None:
    rule map_reads:
        input:
            R1
            R2
            crefG
        output:
        params:
        log:
        shell:

if not convRef and not trimReads is None:
    rule map_reads:
        input:
            R1cut
            R2cut
            crefG
        output:
        params:
        log:
        shell:

if not convRef and not trimReads is None:
    rule map_reads:
        input:
        output:
        params:
        log:
        shell:

rule index_bam:
    input:
    output:
    params:
    log:
    shell:

rule rm_dupes:
    input:
    output:
    params:
    log:
    shell:

rule get_ran_CG:
    input:
    output:
    params:
    log:
    shell:

rule calc_Mbias:
    input:
    output:
    params:
    log:
    shell:

if intList:
    rule depth_of_cov:
        input:
        output:
        params:
        log:
        shell:

else:
    rule depth_of_cov:
        input:
        output:
        params:
        log:
        shell:

if not trimReads is None:
    rule conv_rate:
        input:
        output:
        log:
        shell:

else:
    rule conv_rate:
        input:
        output:
        log:
        shell:

rule get_flagstat:
    input:
    output:
    log:
    shell:

rule produce_report:
    input:
    output:
    params:
    log:
    shell:  

rule methyl_extract:
    input:
    output:
    params:
    log:
    shell:

rule CpG_filt:
    input:
    output:
    params:
    log:
    shell:

if sampleInfo:
    rule CpG_stats:
        input:
        output:
        params:
        log:
        shell:

    rule run_metilene:
        input:
        output:
        params:
        log:
        shell:

    rule get_CG_metilene:
        input:
        output:
        params:
        log:
        shell:

    rule cleanup_metilene:
        input:
        output:
        params:
        log:
        shell:


if intList:
    rule get_CG_per_int:
        input:
        output:
        params:
        log:
        shell:

    if sampleInfo:
        rule intAgg_stats:
            input:
            output:
            params:
            log:
            shell:

 
