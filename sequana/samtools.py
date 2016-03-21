"""



http://www.acgt.me/blog/2014/12/16/understanding-mapq-scores-in-sam-files-does-37-42

http://biofinysics.blogspot.fr/2014/05/how-does-bowtie2-assign-mapq-scores.html


https://gitlab.univ-nantes.fr/a-slide/ContaVect/blob/9a411abfa720064c205c5f6c811afdfea206ed12/pyDNA/pySamTools/Bam.py

pysamtools



Interesting commands::

    samtools flagstat contaminant.bam
    samtools stats contaminant.bam
"""

import pandas as pd
import pylab
import pysam

# pysam uses htlib behing the scene and is very fast
# pysam works great for BAM file but with SAM, it needs to read the file after
# each compete iteration, which is not very useful


class BAM(pysam.AlignmentFile):
    """

    mode rb for bam files

    """
    def __init__(self, filename, mode="rb", *args):
        # works for py27 but not py35 probably a missing __init__  or __new__ in
        # AlignmentFile class. See e.g., stackoverflow/questions/
        # 26653401/typeerror-object-takes-no-parameters-but-only-in-python-3
        #super(BAM, self).__init__(filename, mode, *args)
        pysam.AlignmentFile.__init__(filename, mode, *args)

    def get_read_names(self):
        self.reset()
        names = [this.qname for this in self]
        self.reset()
        return names

    def iter_unmapped_reads(self):
        self.reset()
        unmapped = (this.qname for this in self if this.is_unmapped)
        self.reset()
        return unmapped

    def iter_mapped_reads(self):
        self.reset()
        mapped = (this.qname for this in self if this.is_unmapped is False)
        self.reset()
        return mapped

    def __len__(self):
        self.reset()
        N = len([x for x in self])
        self.reset()
        return N

    def get_stats(self):
        #See samtools stats

        """1526795 + 0 in total (QC-passed reads + QC-failed reads)
        13 + 0 secondary
        0 + 0 supplementary
        0 + 0 duplicates
        3010 + 0 mapped (0.20% : N/A)
        1526782 + 0 paired in sequencing
        763391 + 0 read1
        763391 + 0 read2
        2700 + 0 properly paired (0.18% : N/A)
        2976 + 0 with itself and mate mapped
        21 + 0 singletons (0.00% : N/A)
        0 + 0 with mate mapped to a different chr
        0 + 0 with mate mapped to a different chr (mapQ>=5)
        """

        d = {}
        d['total_reads'] = len(list(self.iter_unmapped_reads()))
        d['mapped_reads'] = len(list(self.iter_mapped_reads()))
        d['unmapped_reads'] = len(list(self.iter_unmapped_reads()))
        d['contamination [%]'] = float(d['mapped_reads']) /float(d['unmapped_reads']) 
        d['contamination [%]'] *= 100
        return d

    def get_flags(self):
        self.reset()
        flags = [s.flag for s in self]
        self.reset()
        return flags

    def get_flags_as_df(self):
        """

            b = BAM(filename)
            df = b.get_flags_as_df()
            df.sum()

        """
        flags = self.get_flags()
        data = [(this, [flag&this for flag in flags]) 
            for this in [1,2,4,8,16,32,64,128,256,512,1024,2048]]
        import pandas as pd
        df = pd.DataFrame(dict(data))
        df = df > 0
        return df


class Alignment(object):
    """Helper class to retrieve info about Alignment

    Takes an alignment as read by :class:`BAM` 

    A segment is a contiguous sequence. A read is a sequence that may consist of
    multiple segments

    * QNAME: a query template name. Reads/segment having same QNAME come from the
      same template. A QNAME set to `*` indicates the information is unavailable.
      In a sam file, a read may occupy multiple alignment 
    * FLAG: combination of bitwise flags. See :class:`SAMFlags`
    * RNAME: reference sequence
    * POS
    * MAPQ: mapping quality if segment is mapped. equals -10 log10 Pr
    * CIGAR: 
    * RNEXT: reference sequence name of the primary alignment of the NEXT read
      in the template
    * PNEXT: position of primary alignment
    * TLEN: signed observed template length
    * SEQ: segment sequence
    * QUAL: ascii of base quality

    """
    def __init__(self, alignment):
        """.. rubric:: constructor

        :param alignment: alignment instance from :class:`BAM`

        ::

            b = BAM()
            s = next(b)
            a = Alignment(s)
            a.as_dict()

        """
        self._data = alignment
        d = self.as_dict()
        for key in d.keys():
            setattr(self, key, d[key])

    def as_dict(self):
        d = {}
        s = self._data
        d['QNAME'] = s.qname
        d['FLAG'] = s.flag
        d['RNAME'] = s.rname
        d['POS'] = s.pos
        d['MAPQ'] = s.mapq
        d['CIGAR'] = s.cigar
        d['PNEXT'] = s.pnext
        d['RNEXT'] = s.rnext
        d['TLEN'] = s.tlen
        d['SEQ'] = s.seq
        d['QUAL'] = s.qual
        return d


class SAMFlags(object):
    """
    """
    def __init__(self, value):
        self.value = value
        self._flags = {
            1: "template having multiple segments in sequencing",
            2: "each segment properly aligned according to the aligner",
            4: "segment unmapped",
            8: "next segment in the template unmapped",
            16: "SEQ being reverse complemented",
            32: "SEQ of the next segment in the template being reverse complemented", 
            64: "the first segment in the template",
            128: "the last segment in the template",
            256: "secondary alignment",
            512: "not passing filters, such as platform/vendor quality controls",
            1024: "PCR or optical duplicate",
            2048: "supplementary alignme"}

    def get_flags(self):
        flags = []
        for this in sorted(self._flags.keys()):
            if self.value & this:
                flags.append(this)
        return flags

    def __str__(self):
        txt = ""
        for this in sorted(self._flags.keys()):
            if self.value & this:
                txt += "%s: %s\n" % (this, self._flags[this])
        return txt


class SAM(pysam.AlignmentFile):
    """

    Header of a SAM file has N lines starting with '@' character.
    Using comment='@' and header None does not make the job.Using skiprows=N
    works but requires to know the number of lines in the header.


    .. todo:: read by chunk size for large files ?
    .. todo:: read two files for comparison ?


    FLAGS SAM format::

        1        0x1     template having multiple segments in sequencing
        2        0x2     each segment properly aligned according to the aligner
        4        0x4     segment unmapped
        8        0x8     next segment in the template unmapped
        16      0x10     SEQ being reverse complemented
        32      0x20     SEQ of the next segment in the template being reverse complemented
        64      0x40     the first segment in the template
        128      0x80    the last segment in the template
        256     0x100    secondary alignment
        512     0x200    not passing filters, such as platform/vendor quality controls
        1024     0x400   PCR or optical duplicate
        2048     0x800   supplementary alignme



    """
    def __init__(self, filename, *args):
        # works for py27 but not py35 probably a missing __init__  or __new__ in
        # AlignmentFile class. See e.g., stackoverflow/questions/
        # 26653401/typeerror-object-takes-no-parameters-but-only-in-python-3
        #super(SAM, self).__init__(filename, mode, *args)
        pysam.AlignmentFile.__init__(filename, *args)
        self.skiprows = self._guess_header_length()

    def _guess_header_length(self):
        with open(self.filename, 'r') as fin:
            skiprows = 0
            while True:
                line = fin.readline()
                if line.startswith('@'):
                    skiprows += 1
                else:
                    break
        return skiprows

    def get_read_names(self):
        return self._get_column(0)

    def _get_column(self, col):
        data = []
        with open(self.filename, "r") as fin:
            for header in range(self.skiprows):
                fin.readline()

            for line in fin:
                data.append(line.split()[col])
        return data

    def plot_mapq_distribution(self):
        """Plot distribution of MAPQ scores (fifth column of SAM)


        The maximum MAPQ value that Bowtie 2 generates is 42 (though it doesn't
        say this anywhere in the documentation). In contrast, the maximum MAPQ
        value that BWA will generate is 37 (though once again, you -
        frustratingly - won't find this information in the manual).

        :reference: http://www.acgt.me/blog/2014/12/16/understanding-mapq-scores-in-sam-files-does-37-42
        """
        pylab.clf()
        data = [float(x) for x in self._get_column(3)]
        pylab.hist(data, bins=100, normed=True)
        pylab.grid(True)
        pylab.xlabel('MAPQ score')
        pylab.ylabel('Fraction of reads')


    def __len__(self):
        self.reset()
        N = len([x for x in self])
        self.reset()
        return N



