from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
from pathlib import Path
import re


def get_size_gc(input_file: str):
    """Function to get sequence size and GC content from fasta_file

    Parameters
    ----------
    input_file : str
        path/to/input/sequence.fasta

    Returns
    -------
    list[str, int, float]
        list containing file key, sequence length and GC%
    """

    FastaFile = open(input_file, "r")
    for rec in SeqIO.parse(FastaFile, "fasta"):
        name = rec.id
        seq = rec.seq
        seqLen = len(rec)
        G_C = gc_fraction(seq)
        sequence_data = [input_file, name, seqLen, G_C]
        return sequence_data


def find_fasta_files(directory_path):
    root_dir = Path(directory_path)
    pattern = r'.*_bin_[0-9]{1,}\.fasta$'
    files = root_dir.rglob('*')
    for file in files:
        if re.match(pattern, file.name):
            return file.resolve()


if __name__ == "__main__":
    fastafiles = find_fasta_files('.')
    data = []
    for path in fastafiles:
        data.append(get_size_gc(str(path)))

    with open('bp_cg.results', 'w') as file:
        file.write(f'{data}\n')
