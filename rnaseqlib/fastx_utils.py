##
## FASTX interface utilities
##
import os
import sys
import time

import rnaseqlib
import rnaseqlib.utils as utils

import rnaseqlib.fasta_utils as fasta_utils
import rnaseqlib.fastq_utils as fastq_utils


def write_open_fastx(fastx_filename):
    """
    Write FASTQ/FASTA file for writing, optionally
    in .gz form.
    """
    fastx_file = None
    if fastx_filename.endswith(".gz"):
        fastx_file = gzip.open(fastx_filename, "wb")
    else:
        fastx_file = open(fastx_filename, "w")
    return fastx_file

##
## Utilities for extracting FASTX sequences
## from BAM files. Not intended for handling
## of paired-end reads.
##
def bam_to_rec(in_file):
    """
    Generator to convert BAM files into Biopython SeqRecords.
    """
    from Bio import SeqIO, Seq, SeqRecord
    bam_file = pysam.Samfile(in_file, "rb")
    for read in bam_file:
        seq = Seq.Seq(read.seq)
        if read.is_reverse:
            seq = seq.reverse_complement()
        rec = SeqRecord.SeqRecord(seq, read.qname, "", "")
        yield rec

def bam_to_fastx(in_file, out_file, record_type="fasta"):
    """
    BAM to FASTX converter, based on code by Brad Chapman.

    By default converts to FASTA record.
    """
    from Bio import SeqIO, Seq, SeqRecord
    out_file = "%s.fa" %(os.path.splitext(in_file)[0])
    out_handle = write_open_fastx(out_file)
    SeqIO.write(bam_to_rec(in_file), out_handle, record_type)
    out_handle.close()


def get_fastx_entries(fastx_filename,
                      fasta=False,
                      fastq=False):
    """
    Get entries of FASTQ/FASTA file.

    if fasta=True, read file as fasta regardless of extension.
    if fastq=True, read file as fastq regardless of extension
    """
    entries = []
    if (fastx_filename.endswith(".fasta") or \
        fastx_filename.endswith(".fa") or \
        fastx_filename.endswith(".fasta.gz")) or fasta:
        # It's a FASTA file
        entries = fasta_utils.read_fasta(fastx_filename)
    elif (fastx_filename.endswith(".fastq") or \
          fastx_filename.endswith(".fq") or \
          fastx_filename.endswith(".fastq.gz")) or fastq:
        # It's a FASTQ file
        entries = fastq_utils.read_fastq(fastx_filename)
    return entries


def fastx_collapse_fastq(fastq_filename, output_dir, logger):
    """
    FASTX collapse FASTQ. Return 
    """
    fastx_collapser = utils.which("fastx_collapser")
    if fastx_collapser is None:
        logger.critical("Could not find fastx_collapser.")
        return None
    if not os.path.isfile(fastq_filename):
        logger.critical("Could not find input fastq %s" \
                        %(fastq_filename))
        return None
    output_basename = \
        utils.trim_fastq_ext(os.path.basename(fastq_filename))
    collapsed_seq_filename = os.path.join(output_dir,
                                          "%s.collapsed.fasta.gz" \
                                          %(output_basename))
    if os.path.isfile(collapsed_seq_filename):
        logger.info("%s exists, skipping collapsing step." \
                    %(collapsed_seq_filename))
        return collapsed_seq_filename
    cat_fastq_cmd = "cat"
    # Handle gzipped input since fastx_collapser does not accept
    # gzipped FASTQ files
    if fastq_filename.endswith(".gz"):
        cat_fastq_cmd = "zcat"
    cat_fastq_cmd += " %s" %(fastq_filename)
    # Use -Q 33 flag to signal Illumina quality scores to
    # FASTX-Toolkit
    fastx_collapser_cmd = "%s | %s -Q 33 | gzip -c - > %s" \
        %(cat_fastq_cmd,
          fastx_collapser,
          collapsed_seq_filename)
    logger.info("Executing: %s" %(fastx_collapser_cmd))
    ret_val = os.system(fastx_collapser_cmd)
    if ret_val != 0:
        logger.critical("Error: fastx_collapser command failed.")
        return None
    return collapsed_seq_filename
                                          
    
