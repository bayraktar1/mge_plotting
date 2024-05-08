from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
from pathlib import Path
import re


def get_size_gc(input_file):
    """Function to get sequence size and GC content from fasta_file

    Parameters
    ----------
    input_file : path object
        path/to/input/sequence.fasta

    Returns
    -------
    list[str, int, float, str, str]
        list containing file key, sequence length, GC%, accession, bin name
    """
    filename = input_file.name
    accession = str(filename).split('_')[0]
    FastaFile = open(input_file, "r")
    for rec in SeqIO.parse(FastaFile, "fasta"):
        name = rec.id
        seq = rec.seq
        seqLen = len(rec)
        G_C = gc_fraction(seq)
        sequence_data = [name, seqLen, G_C, accession, filename]
        return sequence_data


def find_fasta_files(directory_path):
    files_list = []
    root_dir = Path(directory_path)
    pattern = r'.*_bin_[0-9]{1,}\.fasta$'
    files = root_dir.rglob('*')
    for file in files:
        if re.match(pattern, file.name):
            files_list.append(file.resolve())
    return files_list


if __name__ == "__main__":
    fastafiles = find_fasta_files('test_cg')
    data = []
    for path in fastafiles:
        data.append(get_size_gc(path))

    with open('test_cg/bp_cg.results', 'w') as file:
        file.write(f'Plasmid\tSeqLen\tCG\tAccession\tfile\n')
        for row in data:
            file.write(f'{'\t'.join(str(part) for part in row)}\n')
