import os

from sequana import FastA, sequana_data
from sequana.fasta import is_fasta
from easydev import TempFile


def test_format_contigs_denovo():
    # test with a custom fasta
    filename = sequana_data("test_fasta.fasta") 
    contigs = FastA(filename)
    with TempFile(suffix='.fasta') as fh:
        contigs.format_contigs_denovo(fh.name)
    contigs.names
    contigs.lengths
    contigs.comments

def test_fasta_filtering():
    filename = sequana_data("test_fasta_filtering.fa") 
    ff = FastA(filename)
    with TempFile(suffix='.fasta') as fh:
        ff.to_fasta(fh.name)
        ff.save_ctg_to_fasta("A", fh.name)

    with TempFile(suffix='.fasta') as fh:
        ff.filter(fh.name, names_to_exclude=["A", "B"])
        reader = FastA(fh.name)
        assert set(reader.names) == set(["C", "D"])

    ff = FastA(filename)
    with TempFile(suffix='.fasta') as fh:
        ff.filter(fh.name, names_to_keep=["A",])
        reader = FastA(fh.name)
        assert set(reader.names) == set(['A'])


def test_others():
    filename = sequana_data("test_fasta.fasta") 
    ff = FastA(filename)
    assert len(ff) == 16
    assert len(ff.comments) == 16
    assert len(ff.names) == 16
    assert len(ff.sequences) == 16
    assert is_fasta(filename) == True
    ff.get_lengths_as_dict()
    with TempFile(suffix='.fasta') as fh:
        ff.select_random_reads(4, output_filename=fh.name)
        ff.select_random_reads([1,2,3], output_filename=fh.name)
        ff.select_random_reads({1,2,3}, output_filename=fh.name)
    assert ff.get_stats()['N'] == 16
    assert ff.get_stats()['mean_length'] > 454 
    with TempFile(suffix='.fasta') as fh:
        ff.reverse_and_save(fh.name)
        ff.to_fasta(fh.name)
        ff.to_igv_chrom_size(fh.name)
