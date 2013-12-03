#!/usr/bin/env python

#-----------------------------------------------------------------------------
# Copyright (c) 2011-2013, The BIOM Format Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import json
from StringIO import StringIO
from numpy import array, nan

from biom.unit_test import TestCase,main
from biom.parse import (parse_biom_table_str,
        parse_biom_table, 
        parse_classic_table_to_rich_table, convert_biom_to_table,
        convert_table_to_biom, parse_classic_table, generatedby,
        MetadataMap, OBS_META_TYPES, light_parse_biom_sparse,
        direct_parse_key, direct_slice_data, get_axis_indices,
        _direct_slice_data_sparse_obs, _direct_slice_data_sparse_samp,
        _remap_axis_sparse_obs, _remap_axis_sparse_samp)
from biom.table import Table
from biom.exception import BiomParseException

__author__ = "Justin Kuczynski"
__copyright__ = "Copyright 2011-2013, The BIOM Format Development Team"
__credits__ = ["Justin Kuczynski","Daniel McDonald", "Adam Robbins-Pianka"]
__license__ = "BSD"
__url__ = "http://biom-format.org"
__version__ = "1.2.0-dev"
__maintainer__ = "Justin Kuczynski"
__email__ = "justinak@gmail.com"

class ParseTests(TestCase):
    """Tests of parse functions"""

    def setUp(self):
        """define some top-level data"""
        self.legacy_otu_table1 = legacy_otu_table1
        self.otu_table1 = otu_table1
        self.otu_table1_floats=otu_table1_floats
        self.files_to_remove = []
        self.biom_minimal_sparse = biom_minimal_sparse
        
        self.classic_otu_table1_w_tax = classic_otu_table1_w_tax.split('\n')
        self.classic_otu_table1_no_tax = classic_otu_table1_no_tax.split('\n')

    def test_direct_parse_key_object(self):
        """Parse a specific key (eg column, rows, etc)"""
        exp = '''"rows":[
                {"id":"GG_OTU_1", "metadata":null},
                {"id":"GG_OTU_2", "metadata":null},
                {"id":"GG_OTU_3", "metadata":null},
                {"id":"GG_OTU_4", "metadata":null},
                {"id":"GG_OTU_5", "metadata":null}
            ]'''  
        obs = direct_parse_key(biom_minimal_sparse, "rows")
        self.assertEqual(obs, exp)

    def test_direct_parse_key_non_existant(self):
        """test a non existant key"""
        exp = ""
        obs = direct_parse_key(biom_minimal_sparse, "does not exist")
        self.assertEqual(obs, exp)

    def test_direct_parse_key_string(self):
        """direct parse a key:string pair"""
        exp = '"generated_by": "QIIME revision XYZ"'
        obs = direct_parse_key(biom_minimal_sparse, "generated_by")
        self.assertEqual(obs, exp)

    def test_direct_parse_key_int(self):
        """direct parse a key:int pair"""
        test_str = '{"a":{"b":[1,2]},"X":10}'
        exp = '"X":10'
        obs = direct_parse_key(test_str, "X")
        self.assertEqual(obs, exp)

    def test_direct_parse_key_float(self):
        """direct parse a key:float pair"""
        test_str = '{"a":{"b":[1,2]},"X":10.123}'
        exp = '"X":10.123'
        obs = direct_parse_key(test_str, "X")
        self.assertEqual(obs, exp)

    def test_direct_slice_data_sparse_obs(self):
        """Directly slice data entries"""
        keep = [1,3]
        exp = '"data": [[0,0,5],[0,1,1],[0,3,2],[0,4,3],[0,5,1],' \
                       '[1,0,2],[1,1,1],[1,2,1],[1,5,1]], "shape": [2, 6]'
        obs = direct_slice_data(biom_minimal_sparse, keep, 'observations')
        self.assertEqual(obs, exp)

    def test_direct_slice_data_sparse_samp(self):
        """Directly slice data entries"""
        keep = [1,3]
        exp = '"data": [[1,0,1],[1,1,2],[2,1,4],[3,0,1],[4,0,1]], '\
                '"shape": [5, 2]'
        obs = direct_slice_data(biom_minimal_sparse, keep, 'samples')
        self.assertEqual(obs, exp)

    def test_direct_slice_data_sparse_idxerr(self):
        """Directly slice data entries"""
        keep = ['1','7']
        self.assertRaises(IndexError, direct_slice_data, biom_minimal_sparse, 
                          keep, 'samples')

    def test__remap_axis_sparse_obs(self):
        """remap row idx based off of a lookup"""
        lookup = {'5':'3','10':'0'}
        in_tuple1 = "5,2,3"
        in_tuple2 = "10,5,10"
        in_tuple3 = "5,4,6"
        exp1 = "3,2,3"
        exp2 = "0,5,10"
        exp3 = "3,4,6"
        obs1 = _remap_axis_sparse_obs(in_tuple1, lookup)
        obs2 = _remap_axis_sparse_obs(in_tuple2, lookup)
        obs3 = _remap_axis_sparse_obs(in_tuple3, lookup)
        self.assertEqual(obs1, exp1)
        self.assertEqual(obs2, exp2)
        self.assertEqual(obs3, exp3)

    def test__remap_axis_sparse_samp(self):
        """remap row idx based off of a lookup"""
        lookup = {'5':'3','10':'0'}
        in_tuple1 = "5,5,3"
        in_tuple2 = "10,10,10"
        in_tuple3 = "doesn't matter,10,6"
        exp1 = "5,3,3"
        exp2 = "10,0,10"
        exp3 = "doesn't matter,0,6"
        obs1 = _remap_axis_sparse_samp(in_tuple1, lookup)
        obs2 = _remap_axis_sparse_samp(in_tuple2, lookup)
        obs3 = _remap_axis_sparse_samp(in_tuple3, lookup)
        self.assertEqual(obs1, exp1)
        self.assertEqual(obs2, exp2)
        self.assertEqual(obs3, exp3)

    def test__direct_slice_data_sparse_obs(self):
        """keep some data by row"""
        input_chunk = """[[0,2,1], [1,0,5], [1,1,1],
             [1,3,2],[1,4,3],[1,5,1],   [2,2,1],
                [2,3,4],
            [2,4,2],[3,0,2],[3,1,1],[4,1,1], [4,2,1]]"""
        to_keep = set([2,1])
        exp = "[[0,0,5],[0,1,1],[0,3,2],[0,4,3],[0,5,1],"\
               "[1,2,1],[1,3,4],[1,4,2]]"
        obs = _direct_slice_data_sparse_obs(input_chunk, to_keep)
        self.assertEqual(obs, exp)

    def test__direct_slice_data_sparse_samp(self):
        """keep some data by column"""
        input_chunk = """[[0,2,1], [1,0,5], [1,1,1],
             [1,3,2],[1,4,3],[1,5,1],   [2,2,1],
                [2,3,4],
            [2,4,2],[3,0,2],[3,1,1],[4,1,1], [4,2,1]]"""
        to_keep = set([2,1])
        exp = "[[0,1,1],[1,0,1],[2,1,1],[3,0,1],[4,0,1],[4,1,1]]"
        obs = _direct_slice_data_sparse_samp(input_chunk, to_keep)
        self.assertEqual(obs, exp)

    def test_generatedby(self):
        """get a generatedby string"""
        exp = "BIOM-Format %s" % __version__
        obs = generatedby()
        self.assertEqual(obs,exp)

    def test_MetadataMap(self):
        """MetadataMap functions as expected
        
        This method is ported from QIIME (http://www.qiime.org). QIIME is a GPL
        project, but we obtained permission from the authors of this method to
        port it to the BIOM Format project (and keep it under BIOM's BSD
        license).
        """
        s1 = ['#sample\ta\tb', '#comment line to skip',\
              'x \t y \t z ', ' ', '#more skip', 'i\tj\tk']
        exp = ([['x','y','z'],['i','j','k']],\
               ['sample','a','b'],\
               ['comment line to skip','more skip'])
        exp = {'x':{'a':'y','b':'z'},'i':{'a':'j','b':'k'}}
        obs = MetadataMap.fromFile(s1)
        self.assertEqual(obs, exp)
    
        #check that we strip double quotes by default
        s2 = ['#sample\ta\tb', '#comment line to skip',\
              '"x "\t" y "\t z ', ' ', '"#more skip"', 'i\t"j"\tk']
        obs = MetadataMap.fromFile(s2)
        self.assertEqual(obs, exp)

    def test_MetadataMap_w_map_fs(self):
        """MetadataMap functions as expected w process_fns
        
        This method is ported from QIIME (http://www.qiime.org). QIIME is a GPL
        project, but we obtained permission from the authors of this method to
        port it to the BIOM Format project (and keep it under BIOM's BSD
        license).
        """
        s1 = ['#sample\ta\tb', '#comment line to skip',\
              'x \t y \t z ', ' ', '#more skip', 'i\tj\tk']
        exp = ([['x','y','z'],['i','j','k']],\
               ['sample','a','b'],\
               ['comment line to skip','more skip'])
        exp = {'x':{'a':'y','b':'zzz'},'i':{'a':'j','b':'kkk'}}
        process_fns = {'b': lambda x: x*3}
        obs = MetadataMap.fromFile(s1,process_fns=process_fns)
        self.assertEqual(obs, exp)

    def test_MetadataMap_w_header(self):
        """MetadataMap functions as expected w user-provided header
        
        This method is ported from QIIME (http://www.qiime.org). QIIME is a GPL
        project, but we obtained permission from the authors of this method to
        port it to the BIOM Format project (and keep it under BIOM's BSD
        license).
        """
        # number of user-provided headers matches number of columns, and no
        # header line in file
        s1 = ['#comment line to skip',
              'x \t y \t z ', ' ', '#more skip', 'i\tj\tk']
        exp = ([['x','y','z'],['i','j','k']],
               ['sample','a','b'],\
               ['comment line to skip','more skip'])
        exp = {'x':{'a':'y','b':'z'},'i':{'a':'j','b':'k'}}
        header = ['sample','a','b']
        obs = MetadataMap.fromFile(s1,header=header)
        self.assertEqual(obs, exp)
        
        # number of user-provided headers is fewer than number of columns, and
        # no header line in file
        s1 = ['#comment line to skip',
              'x \t y \t z ', ' ', '#more skip', 'i\tj\tk']
        exp = ([['x','y','z'],['i','j','k']],
               ['sample','a'],\
               ['comment line to skip','more skip'])
        exp = {'x':{'a':'y'},'i':{'a':'j'}}
        header = ['sample','a']
        obs = MetadataMap.fromFile(s1,header=header)
        self.assertEqual(obs, exp)
        
        # number of user-provided headers is fewer than number of columns, and
        # header line in file (overridden by user-provided)
        s1 = ['#sample\ta\tb', '#comment line to skip',\
              'x \t y \t z ', ' ', '#more skip', 'i\tj\tk']
        exp = ([['x','y','z'],['i','j','k']],
               ['sample','a'],\
               ['comment line to skip','more skip'])
        exp = {'x':{'a':'y'},'i':{'a':'j'}}
        header = ['sample','a']
        obs = MetadataMap.fromFile(s1,header=header)
        self.assertEqual(obs, exp)

    def test_parse_biom_table_str(self):
        """tests for parse_biom_table_str"""
        # this method is tested through parse_biom_table tests
        pass

    def test_parse_classic_table(self):
        """Parses a classic table
        
        This method is ported from QIIME (http://www.qiime.org). QIIME is a GPL
        project, but we obtained permission from the authors of this method to
        port it to the BIOM Format project (and keep it under BIOM's BSD
        license).
        """
        input = legacy_otu_table1.splitlines()
        samp_ids = ['Fing','Key','NA']
        obs_ids = ['0','1','7','3','4']
        metadata = ['Bacteria; Actinobacteria; Actinobacteridae; Propionibacterineae; Propionibacterium', 'Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Lactobacillales; Lactobacillales; Streptococcaceae; Streptococcus','Bacteria; Actinobacteria; Actinobacteridae; Gordoniaceae; Corynebacteriaceae','Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Staphylococcaceae','Bacteria; Cyanobacteria; Chloroplasts; vectors']
        md_name = 'Consensus Lineage'
        data = array([[19111,44536,42],
                      [1216,3500,6],
                      [1803,1184,2],
                      [1722,4903,17],
                      [589,2074,34]])
       
        exp = (samp_ids,obs_ids,data,metadata,md_name)
        obs = parse_classic_table(input,dtype=int)
        self.assertEqual(obs, exp)

legacy_otu_table1 = """# some comment goes here
#OTU ID	Fing	Key	NA	Consensus Lineage
0	19111	44536	42	Bacteria; Actinobacteria; Actinobacteridae; Propionibacterineae; Propionibacterium

1	1216	3500	6	Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Lactobacillales; Lactobacillales; Streptococcaceae; Streptococcus
7	1803	1184	2	Bacteria; Actinobacteria; Actinobacteridae; Gordoniaceae; Corynebacteriaceae
3	1722	4903	17	Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Staphylococcaceae
4	589	2074	34	Bacteria; Cyanobacteria; Chloroplasts; vectors
"""

otu_table1 = """# Some comment




OTU ID	Fing	Key	NA	Consensus Lineage
0	19111	44536	42	Bacteria; Actinobacteria; Actinobacteridae; Propionibacterineae; Propionibacterium
# some other comment
1	1216	3500	6	Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Lactobacillales; Lactobacillales; Streptococcaceae; Streptococcus
7	1803	1184	2	Bacteria; Actinobacteria; Actinobacteridae; Gordoniaceae; Corynebacteriaceae
# comments
#    everywhere!
3	1722	4903	17	Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Staphylococcaceae
4	589	2074	34	Bacteria; Cyanobacteria; Chloroplasts; vectors
"""

otu_table1_floats = """# Some comment




OTU ID	Fing	Key	NA	Consensus Lineage
0	19111.0	44536.0	42.0	Bacteria; Actinobacteria; Actinobacteridae; Propionibacterineae; Propionibacterium
# some other comment
1	1216.0	3500.0	6.0	Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Lactobacillales; Lactobacillales; Streptococcaceae; Streptococcus
7	1803.0	1184.0	2.0	Bacteria; Actinobacteria; Actinobacteridae; Gordoniaceae; Corynebacteriaceae
# comments
#    everywhere!
3	1722.1	4903.2	17	Bacteria; Firmicutes; Alicyclobacillaceae; Bacilli; Staphylococcaceae
4	589.6	2074.4	34.5	Bacteria; Cyanobacteria; Chloroplasts; vectors
"""

biom_minimal_sparse="""
    {
        "id":null,
        "format": "Biological Observation Matrix v0.9",
        "format_url": "http://some_website/QIIME_MGRAST_dataformat_v0.9.html",
        "type": "OTU table",
        "generated_by": "QIIME revision XYZ",
        "date": "2011-12-19T19:00:00",
        "rows":[
                {"id":"GG_OTU_1", "metadata":null},
                {"id":"GG_OTU_2", "metadata":null},
                {"id":"GG_OTU_3", "metadata":null},
                {"id":"GG_OTU_4", "metadata":null},
                {"id":"GG_OTU_5", "metadata":null}
            ],  
        "columns": [
                {"id":"Sample1", "metadata":null},
                {"id":"Sample2", "metadata":null},
                {"id":"Sample3", "metadata":null},
                {"id":"Sample4", "metadata":null},
                {"id":"Sample5", "metadata":null},
                {"id":"Sample6", "metadata":null}
            ],
        "matrix_type": "sparse",
        "matrix_element_type": "int",
        "shape": [5, 6], 
        "data":[[0,2,1],
                [1,0,5],
                [1,1,1],
                [1,3,2],
                [1,4,3],
                [1,5,1],
                [2,2,1],
                [2,3,4],
                [2,4,2],
                [3,0,2],
                [3,1,1],
                [3,2,1],
                [3,5,1],
                [4,1,1],
                [4,2,1]
               ]
    }
"""

classic_otu_table1_w_tax = """#Full OTU Counts
#OTU ID	PC.354	PC.355	PC.356	PC.481	PC.593	PC.607	PC.634	PC.635	PC.636	Consensus Lineage
0	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
1	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
2	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Porphyromonadaceae;Parabacteroides
3	2	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
4	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
5	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
6	0	0	0	0	0	0	0	1	0	Root;Bacteria;Actinobacteria;Actinobacteria
7	0	0	2	0	0	0	0	0	2	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
8	1	1	0	2	4	0	0	0	0	Root;Bacteria;Firmicutes;Bacilli;Lactobacillales;Lactobacillaceae;Lactobacillus
9	0	0	2	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
10	0	1	0	0	0	0	0	0	0	Root;Bacteria
11	0	0	0	0	0	0	1	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
12	0	0	0	0	0	0	1	0	0	Root;Bacteria;Bacteroidetes
13	1	0	0	1	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
14	0	0	1	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
15	0	0	0	0	1	0	0	0	0	Root;Bacteria
16	1	0	2	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
17	0	0	0	1	0	0	4	10	37	Root;Bacteria;Bacteroidetes
18	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
19	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes
20	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
21	0	0	0	0	0	0	2	3	2	Root;Bacteria;Bacteroidetes
22	0	0	0	0	2	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
23	14	1	14	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Bacilli;Lactobacillales;Lactobacillaceae;Lactobacillus
24	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
25	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
26	0	0	0	0	0	0	0	1	1	Root;Bacteria;Bacteroidetes
27	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes
28	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
29	6	0	4	0	2	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
30	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes
31	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
32	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
33	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
34	0	0	0	0	0	0	8	10	2	Root;Bacteria
35	1	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
36	1	0	1	0	0	0	0	1	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
37	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
38	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
39	0	0	0	0	0	0	0	1	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
40	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
41	0	0	1	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
42	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes
43	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
44	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
45	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Erysipelotrichi;Erysipelotrichales;Erysipelotrichaceae;Coprobacillus
46	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes
47	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
48	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
49	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
50	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
51	0	1	0	0	0	0	0	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
52	0	2	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
53	0	0	0	0	0	0	2	0	1	Root;Bacteria;Proteobacteria;Deltaproteobacteria
54	0	0	0	0	0	0	5	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Porphyromonadaceae;Parabacteroides
55	0	0	0	0	0	0	1	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
56	0	0	0	0	0	1	0	0	0	Root;Bacteria;Bacteroidetes
57	0	0	0	0	0	0	0	1	0	Root;Bacteria
58	1	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
59	0	0	0	0	0	0	0	0	1	Root;Bacteria;Deferribacteres;Deferribacteres;Deferribacterales;Deferribacteraceae;Mucispirillum
60	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
61	0	0	1	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
62	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
63	1	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
64	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
65	0	0	0	6	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
66	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
67	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
68	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
69	0	0	1	0	0	0	0	0	0	Root;Bacteria
70	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
71	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
72	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
73	0	0	0	0	0	5	0	0	0	Root;Bacteria;Bacteroidetes
74	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
75	1	0	1	0	0	0	0	0	0	Root;Bacteria;Bacteroidetes
76	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
77	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
78	1	0	1	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
79	2	3	8	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
80	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Porphyromonadaceae;Parabacteroides
81	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
82	0	0	0	0	0	2	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
83	0	0	0	1	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
84	1	0	0	0	0	0	0	2	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae;Ruminococcus
85	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
86	0	0	0	0	0	0	0	1	0	Root;Bacteria
87	0	0	1	0	0	2	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
88	0	0	0	0	0	0	0	1	0	Root;Bacteria
89	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
90	0	0	0	9	0	0	3	0	0	Root;Bacteria;Firmicutes;Erysipelotrichi;Erysipelotrichales;Erysipelotrichaceae;Turicibacter
91	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Butyrivibrio
92	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
93	0	0	0	0	0	0	2	1	0	Root;Bacteria;Bacteroidetes
94	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
95	0	0	0	2	0	0	0	0	0	Root;Bacteria;Bacteroidetes
96	0	0	0	1	0	1	0	1	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
97	0	0	0	0	0	1	0	0	0	Root;Bacteria
98	0	0	0	0	0	0	0	1	0	Root;Bacteria
99	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
100	0	0	0	1	0	0	0	0	0	Root;Bacteria
101	0	0	0	3	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
102	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
103	0	1	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
104	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
105	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
106	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
107	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
108	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Incertae Sedis XIII;Anaerovorax
109	0	0	0	1	0	0	1	5	2	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
110	0	0	0	0	0	2	0	0	0	Root;Bacteria;Actinobacteria;Actinobacteria;Coriobacteridae;Coriobacteriales;Coriobacterineae;Coriobacteriaceae;Olsenella
111	0	0	0	0	0	0	1	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
112	0	0	0	0	0	0	1	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
113	0	0	0	0	0	1	0	0	0	Root;Bacteria
114	0	0	0	0	0	1	0	0	0	Root;Bacteria
115	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes
116	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
117	1	0	2	0	0	6	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
118	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
119	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
120	1	3	1	2	1	9	2	4	5	Root;Bacteria;Bacteroidetes
121	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
122	0	0	0	1	0	2	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
123	0	0	0	0	0	0	1	0	0	Root;Bacteria;Actinobacteria;Actinobacteria;Coriobacteridae;Coriobacteriales;Coriobacterineae;Coriobacteriaceae
124	0	0	0	0	0	0	1	0	0	Root;Bacteria;Actinobacteria;Actinobacteria;Coriobacteridae;Coriobacteriales;Coriobacterineae;Coriobacteriaceae
125	0	0	0	0	0	0	1	0	0	Root;Bacteria;Bacteroidetes
126	0	0	2	0	0	0	0	1	0	Root;Bacteria
127	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
128	0	0	0	0	0	0	1	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
129	0	0	0	1	0	0	0	0	0	Root;Bacteria
130	0	0	0	0	5	2	0	0	0	Root;Bacteria;Proteobacteria;Epsilonproteobacteria;Campylobacterales;Helicobacteraceae;Helicobacter
131	0	0	1	3	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
132	0	0	0	0	1	0	0	0	0	Root;Bacteria
133	0	0	1	0	0	0	0	0	0	Root;Bacteria
134	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
135	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
136	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
137	0	0	0	0	0	0	0	1	0	Root;Bacteria
138	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
139	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
140	0	0	0	0	0	0	1	3	0	Root;Bacteria
141	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
142	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
143	0	0	1	0	0	0	0	0	0	Root;Bacteria
144	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
145	0	0	2	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
146	1	0	0	0	2	0	2	0	3	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
147	0	1	0	1	1	0	0	0	3	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
148	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes
149	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
150	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
151	0	0	0	1	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
152	0	0	0	1	0	0	1	2	19	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
153	0	2	1	2	0	0	1	1	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
154	2	18	0	1	0	0	21	4	4	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
155	0	0	0	0	0	5	9	5	3	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
156	0	0	1	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
157	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
158	1	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
159	0	0	0	0	0	0	0	1	1	Root;Bacteria;Bacteroidetes
160	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
161	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
162	0	0	0	0	0	3	5	2	6	Root;Bacteria;Deferribacteres;Deferribacteres;Deferribacterales;Deferribacteraceae;Mucispirillum
163	0	0	0	0	0	0	0	0	1	Root;Bacteria
164	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
165	2	1	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
166	0	0	0	0	0	0	0	1	0	Root;Bacteria
167	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
168	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
169	0	2	0	7	0	0	0	2	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
170	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
171	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
172	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
173	0	0	0	0	0	1	0	0	0	Root;Bacteria
174	1	0	0	0	10	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Peptostreptococcaceae;Peptostreptococcaceae Incertae Sedis
175	0	0	0	0	1	0	0	0	0	Root;Bacteria;Bacteroidetes
176	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
177	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia
178	0	0	0	2	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
179	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
180	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
181	1	4	2	6	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
182	0	0	0	0	0	1	0	0	0	Root;Bacteria
183	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia
184	0	0	0	1	0	0	3	1	0	Root;Bacteria;Bacteroidetes
185	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
186	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
187	0	1	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
188	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
189	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
190	0	0	0	0	0	0	0	1	0	Root;Bacteria
191	2	1	10	2	24	0	0	1	1	Root;Bacteria
192	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Bacilli;Lactobacillales;Streptococcaceae;Streptococcus
193	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Butyrivibrio
194	0	0	2	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae;Acetanaerobacterium
195	0	0	0	0	0	1	0	0	0	Root;Bacteria
196	0	0	0	0	0	1	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
197	0	1	0	0	0	0	0	0	0	Root;Bacteria
198	0	2	0	0	0	1	0	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales
199	0	0	0	0	0	1	1	0	0	Root;Bacteria
200	0	0	0	2	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
201	0	0	0	1	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
202	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
203	0	2	2	4	0	5	1	5	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
204	1	4	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
205	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
206	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
207	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
208	0	2	0	2	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
209	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
210	0	0	0	0	0	0	0	0	1	Root;Bacteria
211	1	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
212	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
213	0	0	0	0	0	0	0	2	0	Root;Bacteria;Firmicutes
214	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
215	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
216	0	0	0	0	0	0	0	1	0	Root;Bacteria;Bacteroidetes
217	0	0	0	0	0	2	0	1	0	Root;Bacteria
218	0	0	0	0	9	1	0	0	0	Root;Bacteria;Bacteroidetes
219	0	0	0	0	1	0	0	0	0	Root;Bacteria
220	1	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
221	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes
222	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
223	0	0	0	0	0	0	0	2	2	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
224	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
225	0	2	1	0	0	0	0	0	0	Root;Bacteria;Bacteroidetes
226	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
227	0	1	2	0	9	1	1	1	3	Root;Bacteria;Bacteroidetes
228	16	0	0	0	12	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
229	0	0	0	0	0	1	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Incertae Sedis XIII
230	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
231	0	19	2	0	2	0	3	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
232	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
233	0	0	0	0	1	0	0	0	0	Root;Bacteria;Bacteroidetes
234	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Bacilli;Lactobacillales;Lactobacillaceae;Lactobacillus
235	0	1	1	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
236	0	0	0	0	0	2	0	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales
237	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
238	0	0	0	0	0	0	0	1	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
239	0	0	0	0	0	1	0	0	0	Root;Bacteria
240	0	0	0	0	0	1	0	0	0	Root;Bacteria
241	0	0	0	0	0	0	2	0	0	Root;Bacteria;TM7;TM7_genera_incertae_sedis
242	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
243	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
244	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes
245	0	0	0	1	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
246	0	0	0	0	0	0	0	1	0	Root;Bacteria
247	0	0	1	0	0	0	0	0	0	Root;Bacteria;Bacteroidetes
248	1	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Bacilli;Lactobacillales;Lactobacillaceae;Lactobacillus
249	1	0	0	0	0	0	0	0	0	Root;Bacteria
250	1	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
251	0	0	0	1	4	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
252	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
253	0	0	0	0	2	0	0	5	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
254	11	13	6	13	2	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
255	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
256	0	0	0	0	0	0	1	0	0	Root;Bacteria
257	0	0	0	0	0	0	5	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
258	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
259	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
260	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
261	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
262	0	1	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Bryantella
263	0	0	0	0	1	0	0	0	0	Root;Bacteria
264	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
265	0	0	0	0	0	2	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
266	0	0	0	2	0	0	0	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae;Alistipes
267	1	0	0	5	17	20	0	0	0	Root;Bacteria
268	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
269	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
270	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
271	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
272	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
273	0	0	0	0	0	0	1	0	0	Root;Bacteria
274	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
275	0	0	0	0	0	0	1	0	0	Root;Bacteria;Verrucomicrobia;Verrucomicrobiae;Verrucomicrobiales;Verrucomicrobiaceae;Akkermansia
276	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
277	1	0	0	0	0	0	0	0	0	Root;Bacteria
278	0	0	0	0	0	1	0	0	0	Root;Bacteria
279	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
280	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
281	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
282	0	0	0	0	0	0	2	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Porphyromonadaceae;Parabacteroides
283	0	0	0	0	0	0	2	1	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
284	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
285	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
286	0	2	3	1	4	0	5	0	4	Root;Bacteria;Bacteroidetes
287	0	0	0	0	0	0	1	1	1	Root;Bacteria;Bacteroidetes
288	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
289	0	0	0	0	3	0	0	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
290	0	0	0	0	0	0	0	0	2	Root;Bacteria;Firmicutes;Bacilli;Bacillales;Staphylococcaceae;Staphylococcus
291	0	0	0	0	1	0	0	0	0	Root;Bacteria
292	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
293	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
294	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
295	29	1	10	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
296	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
297	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
298	0	0	0	0	0	0	1	0	0	Root;Bacteria;Actinobacteria;Actinobacteria
299	0	0	0	0	0	0	1	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
300	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia
301	0	0	0	0	0	0	2	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
302	0	0	0	0	0	1	0	0	0	Root;Bacteria
303	0	0	0	0	0	0	0	0	1	Root;Bacteria
304	0	0	0	0	0	0	0	1	0	Root;Bacteria;Bacteroidetes
305	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
306	0	0	0	0	0	0	0	0	1	Root;Bacteria
307	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
308	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae;Ruminococcaceae Incertae Sedis
309	0	0	0	1	0	0	0	0	0	Root;Bacteria;Actinobacteria;Actinobacteria;Coriobacteridae;Coriobacteriales;Coriobacterineae;Coriobacteriaceae;Denitrobacterium
310	0	0	1	0	0	0	0	0	0	Root;Bacteria
311	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
312	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
313	0	1	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Porphyromonadaceae;Parabacteroides
314	0	0	1	0	0	0	0	0	0	Root;Bacteria;Bacteroidetes
315	1	3	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
316	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
317	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
318	0	0	0	0	0	1	0	0	0	Root;Bacteria;Proteobacteria
319	0	2	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
320	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
321	0	0	0	0	0	0	0	0	1	Root;Bacteria
322	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
323	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
324	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
325	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
326	0	0	0	0	4	0	0	0	2	Root;Bacteria;Firmicutes;Erysipelotrichi;Erysipelotrichales;Erysipelotrichaceae;Erysipelotrichaceae Incertae Sedis
327	0	0	0	0	0	0	0	1	0	Root;Bacteria;Bacteroidetes
328	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
329	2	2	0	1	0	0	0	0	0	Root;Bacteria;Bacteroidetes
330	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes
331	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes
332	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
333	0	0	0	0	0	6	0	3	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
334	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
335	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
336	0	0	1	0	0	0	0	0	0	Root;Bacteria
337	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
338	0	0	0	0	0	0	0	1	0	Root;Bacteria
339	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
340	0	0	2	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
341	0	0	1	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
342	0	0	0	0	0	1	0	0	0	Root;Bacteria
343	0	0	0	0	0	0	0	0	1	Root;Bacteria;Actinobacteria;Actinobacteria;Coriobacteridae;Coriobacteriales;Coriobacterineae;Coriobacteriaceae
344	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
345	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
346	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
347	0	0	0	1	0	0	0	0	0	Root;Bacteria
348	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
349	0	0	0	0	0	0	1	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
350	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
351	0	0	0	0	2	2	1	4	1	Root;Bacteria;Bacteroidetes
352	3	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
353	0	4	4	0	1	2	0	2	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
354	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
355	0	0	0	0	0	0	0	1	0	Root;Bacteria
356	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
357	0	0	0	4	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
358	0	0	1	0	0	0	0	0	0	Root;Bacteria
359	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
360	0	0	1	0	0	0	0	1	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
361	2	0	2	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
362	1	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
363	0	0	0	0	0	1	0	1	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Rikenellaceae
364	1	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
365	0	0	0	0	0	2	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
366	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Roseburia
367	0	0	0	0	1	0	0	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
368	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
369	0	0	0	0	0	1	0	0	0	Root;Bacteria
370	2	1	0	5	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
371	1	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
372	0	1	0	0	0	0	0	0	0	Root;Bacteria
373	0	1	0	0	0	0	3	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Clostridiaceae;Clostridiaceae 1;Clostridium
374	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
375	0	0	0	0	0	0	4	0	0	Root;Bacteria;Firmicutes;Erysipelotrichi;Erysipelotrichales;Erysipelotrichaceae;Erysipelotrichaceae Incertae Sedis
376	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
377	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
378	0	0	0	0	0	0	0	0	1	Root;Bacteria;Bacteroidetes
379	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Ruminococcaceae
380	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Bacilli;Bacillales;Staphylococcaceae;Staphylococcus
381	0	0	2	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
382	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
383	4	9	0	2	0	0	0	2	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
384	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
385	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Bacilli;Lactobacillales;Carnobacteriaceae;Carnobacteriaceae 1
386	0	0	1	0	0	0	0	0	0	Root;Bacteria
387	0	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
388	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
389	0	1	0	0	0	0	0	0	0	Root;Bacteria
390	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
391	0	0	0	0	0	0	0	0	1	Root;Bacteria;Firmicutes
392	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
393	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
394	0	0	1	0	0	0	0	0	0	Root;Bacteria
395	1	1	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
396	2	0	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
397	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
398	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
399	0	0	0	0	0	0	13	0	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Bacteroidaceae;Bacteroides
400	0	0	0	0	0	0	1	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
401	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
402	0	1	0	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
403	0	0	0	0	0	0	0	1	0	Root;Bacteria;Bacteroidetes;Bacteroidetes;Bacteroidales;Prevotellaceae
404	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae;Lachnospiraceae Incertae Sedis
405	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
406	0	0	0	0	0	1	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
407	1	0	0	0	0	4	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
408	1	5	3	2	0	0	0	0	1	Root;Bacteria;Bacteroidetes
409	0	0	0	0	0	0	0	1	1	Root;Bacteria;Bacteroidetes
410	0	0	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
411	0	0	0	1	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
412	0	0	0	0	2	0	0	0	0	Root;Bacteria;Bacteroidetes
413	0	0	0	0	0	0	0	1	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales
414	1	0	1	0	0	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales;Lachnospiraceae
415	0	0	0	0	0	7	0	2	2	Root;Bacteria;Bacteroidetes
416	0	1	0	0	1	0	0	0	0	Root;Bacteria;Firmicutes;Clostridia;Clostridiales"""

classic_otu_table1_no_tax = """#Full OTU Counts
#OTU ID	PC.354	PC.355	PC.356	PC.481	PC.593	PC.607	PC.634	PC.635	PC.636
0	0	0	0	0	0	0	0	1	0
1	0	0	0	0	0	1	0	0	0
2	0	0	0	0	0	0	0	0	1
3	2	1	0	0	0	0	0	0	0
4	1	0	0	0	0	0	0	0	0
5	0	0	0	0	0	0	0	0	1
6	0	0	0	0	0	0	0	1	0
7	0	0	2	0	0	0	0	0	2
8	1	1	0	2	4	0	0	0	0
9	0	0	2	0	0	0	0	0	0
10	0	1	0	0	0	0	0	0	0
11	0	0	0	0	0	0	1	0	0
12	0	0	0	0	0	0	1	0	0
13	1	0	0	1	0	1	0	0	0
14	0	0	1	1	0	0	0	0	0
15	0	0	0	0	1	0	0	0	0
16	1	0	2	0	0	0	0	0	0
17	0	0	0	1	0	0	4	10	37
18	0	1	0	0	0	0	0	0	0
19	0	0	0	0	0	0	0	0	1
20	0	0	0	0	1	0	0	0	0
21	0	0	0	0	0	0	2	3	2
22	0	0	0	0	2	0	1	0	0
23	14	1	14	1	0	0	0	0	0
24	1	0	0	0	0	0	0	0	0
25	0	0	0	1	0	0	0	0	0
26	0	0	0	0	0	0	0	1	1
27	0	0	0	0	0	0	0	0	1
28	0	1	0	0	0	0	0	0	0
29	6	0	4	0	2	0	0	0	0
30	0	0	0	0	0	1	0	0	0
31	1	0	0	0	0	0	0	0	0
32	0	0	0	0	1	0	0	0	0
33	0	0	0	1	0	0	0	0	0
34	0	0	0	0	0	0	8	10	2
35	1	0	1	0	0	0	0	0	0
36	1	0	1	0	0	0	0	1	1
37	0	0	0	0	0	1	0	0	0
38	0	0	1	0	0	0	0	0	0
39	0	0	0	0	0	0	0	1	0
40	0	0	1	0	0	0	0	0	0
41	0	0	1	0	0	0	0	1	0
42	0	0	0	0	0	1	0	0	0
43	0	0	0	0	0	1	0	0	0
44	0	0	1	0	0	0	0	0	0
45	1	0	0	0	0	0	0	0	0
46	0	0	0	0	0	0	0	0	1
47	0	0	0	1	0	0	0	0	0
48	0	0	0	0	1	0	0	0	0
49	0	0	0	1	0	0	0	0	0
50	0	1	0	0	0	0	0	0	0
51	0	1	0	0	0	0	0	0	0
52	0	2	0	0	0	0	0	0	0
53	0	0	0	0	0	0	2	0	1
54	0	0	0	0	0	0	5	0	0
55	0	0	0	0	0	0	1	0	0
56	0	0	0	0	0	1	0	0	0
57	0	0	0	0	0	0	0	1	0
58	1	0	1	0	0	0	0	0	0
59	0	0	0	0	0	0	0	0	1
60	0	0	0	0	0	0	0	1	0
61	0	0	1	0	0	0	0	1	0
62	0	0	1	0	0	0	0	0	0
63	1	0	1	0	0	0	0	0	0
64	0	0	0	0	0	0	0	0	1
65	0	0	0	6	0	0	0	1	0
66	0	0	1	0	0	0	0	0	0
67	0	0	1	0	0	0	0	0	0
68	1	0	0	0	0	0	0	0	0
69	0	0	1	0	0	0	0	0	0
70	0	0	0	0	0	1	0	0	0
71	0	0	1	0	0	0	0	0	0
72	0	0	0	0	0	1	0	0	0
73	0	0	0	0	0	5	0	0	0
74	0	0	0	1	0	0	0	0	0
75	1	0	1	0	0	0	0	0	0
76	0	0	0	1	0	0	0	0	0
77	0	0	0	1	0	0	0	0	0
78	1	0	1	1	0	0	0	0	0
79	2	3	8	0	1	0	0	0	0
80	0	0	0	0	0	0	0	0	1
81	1	0	0	0	0	0	0	0	0
82	0	0	0	0	0	2	0	0	0
83	0	0	0	1	0	0	0	1	0
84	1	0	0	0	0	0	0	2	0
85	0	0	0	0	0	0	0	0	1
86	0	0	0	0	0	0	0	1	0
87	0	0	1	0	0	2	0	1	0
88	0	0	0	0	0	0	0	1	0
89	0	0	1	0	0	0	0	0	0
90	0	0	0	9	0	0	3	0	0
91	0	0	0	1	0	0	0	0	0
92	0	0	0	0	0	0	1	0	0
93	0	0	0	0	0	0	2	1	0
94	0	0	0	0	0	0	0	1	0
95	0	0	0	2	0	0	0	0	0
96	0	0	0	1	0	1	0	1	1
97	0	0	0	0	0	1	0	0	0
98	0	0	0	0	0	0	0	1	0
99	0	0	0	1	0	0	0	0	0
100	0	0	0	1	0	0	0	0	0
101	0	0	0	3	0	0	0	0	0
102	0	1	0	0	0	0	0	0	0
103	0	1	0	0	0	0	1	0	0
104	0	0	0	0	0	1	0	0	0
105	0	1	0	0	0	0	0	0	0
106	0	0	0	0	0	1	0	0	0
107	0	0	0	0	0	1	0	0	0
108	0	0	0	0	0	0	1	0	0
109	0	0	0	1	0	0	1	5	2
110	0	0	0	0	0	2	0	0	0
111	0	0	0	0	0	0	1	0	0
112	0	0	0	0	0	0	1	0	0
113	0	0	0	0	0	1	0	0	0
114	0	0	0	0	0	1	0	0	0
115	0	0	0	0	0	1	0	0	0
116	0	1	0	0	0	0	0	0	0
117	1	0	2	0	0	6	0	0	0
118	0	0	0	1	0	0	0	0	0
119	0	0	0	0	0	0	0	1	0
120	1	3	1	2	1	9	2	4	5
121	0	0	0	0	0	0	0	1	0
122	0	0	0	1	0	2	0	0	0
123	0	0	0	0	0	0	1	0	0
124	0	0	0	0	0	0	1	0	0
125	0	0	0	0	0	0	1	0	0
126	0	0	2	0	0	0	0	1	0
127	0	0	0	0	0	1	0	0	0
128	0	0	0	0	0	0	1	0	0
129	0	0	0	1	0	0	0	0	0
130	0	0	0	0	5	2	0	0	0
131	0	0	1	3	0	0	0	0	0
132	0	0	0	0	1	0	0	0	0
133	0	0	1	0	0	0	0	0	0
134	0	0	0	0	0	0	0	0	1
135	0	0	1	0	0	0	0	0	0
136	1	0	0	0	0	0	0	0	0
137	0	0	0	0	0	0	0	1	0
138	0	0	1	0	0	0	0	0	0
139	1	0	0	0	0	0	0	0	0
140	0	0	0	0	0	0	1	3	0
141	0	0	0	0	1	0	0	0	0
142	0	0	0	0	1	0	0	0	0
143	0	0	1	0	0	0	0	0	0
144	0	0	0	0	0	1	0	0	0
145	0	0	2	0	0	0	0	0	0
146	1	0	0	0	2	0	2	0	3
147	0	1	0	1	1	0	0	0	3
148	0	0	0	0	0	1	0	0	0
149	0	0	0	0	0	0	0	1	0
150	0	0	0	0	1	0	0	0	0
151	0	0	0	1	0	0	0	1	0
152	0	0	0	1	0	0	1	2	19
153	0	2	1	2	0	0	1	1	1
154	2	18	0	1	0	0	21	4	4
155	0	0	0	0	0	5	9	5	3
156	0	0	1	0	0	0	0	1	0
157	0	0	1	0	0	0	0	0	0
158	1	0	1	0	0	0	0	0	0
159	0	0	0	0	0	0	0	1	1
160	0	0	0	0	0	0	1	0	0
161	0	0	1	0	0	0	0	0	0
162	0	0	0	0	0	3	5	2	6
163	0	0	0	0	0	0	0	0	1
164	0	0	0	0	0	1	0	0	0
165	2	1	1	0	0	0	0	0	0
166	0	0	0	0	0	0	0	1	0
167	1	0	0	0	0	0	0	0	0
168	0	0	0	1	0	0	0	0	0
169	0	2	0	7	0	0	0	2	0
170	0	0	0	1	0	0	0	0	0
171	0	0	0	1	0	0	0	0	0
172	1	0	0	0	0	0	0	0	0
173	0	0	0	0	0	1	0	0	0
174	1	0	0	0	10	0	0	0	0
175	0	0	0	0	1	0	0	0	0
176	0	0	0	0	0	1	0	0	0
177	0	0	0	1	0	0	0	0	0
178	0	0	0	2	0	0	0	0	0
179	0	0	0	1	0	0	0	0	0
180	0	0	0	0	1	0	0	0	0
181	1	4	2	6	0	0	0	0	0
182	0	0	0	0	0	1	0	0	0
183	0	0	0	0	0	0	1	0	0
184	0	0	0	1	0	0	3	1	0
185	0	0	0	0	0	0	0	0	1
186	0	0	1	0	0	0	0	0	0
187	0	1	0	0	0	0	0	0	1
188	0	0	0	0	0	0	0	1	0
189	0	0	0	1	0	0	0	0	0
190	0	0	0	0	0	0	0	1	0
191	2	1	10	2	24	0	0	1	1
192	0	0	0	0	0	1	0	0	0
193	0	0	0	0	0	1	0	0	0
194	0	0	2	0	0	0	0	0	0
195	0	0	0	0	0	1	0	0	0
196	0	0	0	0	0	1	0	1	0
197	0	1	0	0	0	0	0	0	0
198	0	2	0	0	0	1	0	0	0
199	0	0	0	0	0	1	1	0	0
200	0	0	0	2	0	0	0	0	0
201	0	0	0	1	0	1	0	0	0
202	0	0	0	0	0	0	1	0	0
203	0	2	2	4	0	5	1	5	0
204	1	4	0	1	0	0	0	0	0
205	0	0	0	0	0	0	0	1	0
206	0	1	0	0	0	0	0	0	0
207	0	0	0	0	0	0	0	1	0
208	0	2	0	2	0	0	0	1	0
209	0	0	1	0	0	0	0	0	0
210	0	0	0	0	0	0	0	0	1
211	1	0	0	1	0	0	0	0	0
212	0	0	0	0	0	0	0	0	1
213	0	0	0	0	0	0	0	2	0
214	0	0	0	0	0	0	0	1	0
215	0	0	0	0	0	0	0	1	0
216	0	0	0	0	0	0	0	1	0
217	0	0	0	0	0	2	0	1	0
218	0	0	0	0	9	1	0	0	0
219	0	0	0	0	1	0	0	0	0
220	1	0	0	0	1	0	0	0	0
221	0	0	0	0	0	0	0	1	0
222	0	1	0	0	0	0	0	0	0
223	0	0	0	0	0	0	0	2	2
224	0	0	0	1	0	0	0	0	0
225	0	2	1	0	0	0	0	0	0
226	0	0	0	0	0	1	0	0	0
227	0	1	2	0	9	1	1	1	3
228	16	0	0	0	12	0	0	0	0
229	0	0	0	0	0	1	1	0	0
230	0	0	0	1	0	0	0	0	0
231	0	19	2	0	2	0	3	0	0
232	0	0	0	0	0	0	1	0	0
233	0	0	0	0	1	0	0	0	0
234	0	0	0	0	1	0	0	0	0
235	0	1	1	0	1	0	0	0	0
236	0	0	0	0	0	2	0	0	0
237	0	0	0	0	1	0	0	0	0
238	0	0	0	0	0	0	0	1	0
239	0	0	0	0	0	1	0	0	0
240	0	0	0	0	0	1	0	0	0
241	0	0	0	0	0	0	2	0	0
242	0	0	0	0	0	0	1	0	0
243	0	0	0	0	0	0	1	0	0
244	0	0	0	0	0	0	0	0	1
245	0	0	0	1	0	0	0	1	0
246	0	0	0	0	0	0	0	1	0
247	0	0	1	0	0	0	0	0	0
248	1	0	0	1	0	0	0	0	0
249	1	0	0	0	0	0	0	0	0
250	1	0	0	0	0	0	0	1	0
251	0	0	0	1	4	0	0	0	0
252	0	0	0	1	0	0	0	0	0
253	0	0	0	0	2	0	0	5	0
254	11	13	6	13	2	0	0	0	0
255	0	0	0	0	0	1	0	0	0
256	0	0	0	0	0	0	1	0	0
257	0	0	0	0	0	0	5	0	0
258	0	0	1	0	0	0	0	0	0
259	0	0	0	0	0	0	0	1	0
260	0	0	0	0	0	0	0	1	0
261	0	0	0	0	0	0	0	1	0
262	0	1	0	0	0	0	0	0	1
263	0	0	0	0	1	0	0	0	0
264	0	0	0	0	0	1	0	0	0
265	0	0	0	0	0	2	0	0	0
266	0	0	0	2	0	0	0	0	0
267	1	0	0	5	17	20	0	0	0
268	0	0	0	0	0	0	1	0	0
269	0	0	0	1	0	0	0	0	0
270	0	0	1	0	0	0	0	0	0
271	0	0	0	0	0	0	0	0	1
272	0	0	0	1	0	0	0	0	0
273	0	0	0	0	0	0	1	0	0
274	0	0	0	0	0	0	1	0	0
275	0	0	0	0	0	0	1	0	0
276	0	0	0	0	0	0	0	1	0
277	1	0	0	0	0	0	0	0	0
278	0	0	0	0	0	1	0	0	0
279	0	0	0	0	0	1	0	0	0
280	0	1	0	0	0	0	0	0	0
281	1	0	0	0	0	0	0	0	0
282	0	0	0	0	0	0	2	0	0
283	0	0	0	0	0	0	2	1	0
284	0	0	0	1	0	0	0	0	0
285	0	0	0	0	0	0	1	0	0
286	0	2	3	1	4	0	5	0	4
287	0	0	0	0	0	0	1	1	1
288	0	0	0	0	0	1	0	0	0
289	0	0	0	0	3	0	0	0	0
290	0	0	0	0	0	0	0	0	2
291	0	0	0	0	1	0	0	0	0
292	0	0	0	0	1	0	0	0	0
293	0	0	0	0	0	1	0	0	0
294	0	1	0	0	0	0	0	0	0
295	29	1	10	0	0	0	0	0	0
296	0	0	0	0	1	0	0	0	0
297	0	0	0	1	0	0	0	0	0
298	0	0	0	0	0	0	1	0	0
299	0	0	0	0	0	0	1	0	1
300	0	0	0	0	0	1	0	0	0
301	0	0	0	0	0	0	2	0	0
302	0	0	0	0	0	1	0	0	0
303	0	0	0	0	0	0	0	0	1
304	0	0	0	0	0	0	0	1	0
305	1	0	0	0	0	0	0	0	0
306	0	0	0	0	0	0	0	0	1
307	0	0	1	0	0	0	0	0	0
308	0	1	0	0	0	0	0	0	0
309	0	0	0	1	0	0	0	0	0
310	0	0	1	0	0	0	0	0	0
311	0	0	0	0	0	1	0	0	0
312	0	0	1	0	0	0	0	0	0
313	0	1	0	0	0	0	0	0	1
314	0	0	1	0	0	0	0	0	0
315	1	3	1	0	0	0	0	0	0
316	0	1	0	0	0	0	0	0	0
317	0	0	0	0	0	0	1	0	0
318	0	0	0	0	0	1	0	0	0
319	0	2	1	0	0	0	0	0	0
320	0	0	0	1	0	0	0	0	0
321	0	0	0	0	0	0	0	0	1
322	0	0	0	1	0	0	0	0	0
323	0	0	1	0	0	0	0	0	0
324	0	0	1	0	0	0	0	0	0
325	0	1	0	0	0	0	0	0	0
326	0	0	0	0	4	0	0	0	2
327	0	0	0	0	0	0	0	1	0
328	0	0	0	1	0	0	0	0	0
329	2	2	0	1	0	0	0	0	0
330	0	0	1	0	0	0	0	0	0
331	0	0	0	0	1	0	0	0	0
332	0	1	0	0	0	0	0	0	0
333	0	0	0	0	0	6	0	3	0
334	1	0	0	0	0	0	0	0	0
335	0	0	0	0	0	0	0	1	0
336	0	0	1	0	0	0	0	0	0
337	0	0	0	1	0	0	0	0	0
338	0	0	0	0	0	0	0	1	0
339	0	0	1	0	0	0	0	0	0
340	0	0	2	0	0	0	0	0	0
341	0	0	1	0	0	0	0	1	0
342	0	0	0	0	0	1	0	0	0
343	0	0	0	0	0	0	0	0	1
344	0	0	1	0	0	0	0	0	0
345	1	0	0	0	0	0	0	0	0
346	0	1	0	0	0	0	0	0	0
347	0	0	0	1	0	0	0	0	0
348	0	0	0	1	0	0	0	0	0
349	0	0	0	0	0	0	1	0	1
350	1	0	0	0	0	0	0	0	0
351	0	0	0	0	2	2	1	4	1
352	3	0	0	0	0	0	0	0	0
353	0	4	4	0	1	2	0	2	1
354	0	0	0	0	0	1	0	0	0
355	0	0	0	0	0	0	0	1	0
356	0	0	0	0	0	1	0	0	0
357	0	0	0	4	0	0	0	0	0
358	0	0	1	0	0	0	0	0	0
359	0	0	1	0	0	0	0	0	0
360	0	0	1	0	0	0	0	1	1
361	2	0	2	1	0	0	0	0	0
362	1	0	0	1	0	0	0	0	0
363	0	0	0	0	0	1	0	1	0
364	1	0	0	0	0	0	0	0	0
365	0	0	0	0	0	2	0	0	0
366	0	0	0	1	0	0	0	0	0
367	0	0	0	0	1	0	0	0	0
368	0	0	0	0	0	1	0	0	0
369	0	0	0	0	0	1	0	0	0
370	2	1	0	5	0	1	0	0	0
371	1	1	0	0	0	0	0	0	0
372	0	1	0	0	0	0	0	0	0
373	0	1	0	0	0	0	3	0	0
374	0	0	0	0	0	0	1	0	0
375	0	0	0	0	0	0	4	0	0
376	0	0	0	0	0	0	0	0	1
377	0	0	0	0	0	0	0	1	0
378	0	0	0	0	0	0	0	0	1
379	0	0	0	0	0	1	0	0	0
380	0	0	0	0	0	0	0	0	1
381	0	0	2	0	0	0	0	0	0
382	0	0	0	0	0	0	0	1	0
383	4	9	0	2	0	0	0	2	0
384	0	0	1	0	0	0	0	0	0
385	0	0	0	0	0	0	0	0	1
386	0	0	1	0	0	0	0	0	0
387	0	0	1	0	0	0	0	0	0
388	0	0	0	1	0	0	0	0	0
389	0	1	0	0	0	0	0	0	0
390	0	0	0	0	0	0	0	0	1
391	0	0	0	0	0	0	0	0	1
392	0	1	0	0	0	0	0	0	0
393	0	0	0	0	0	1	0	0	0
394	0	0	1	0	0	0	0	0	0
395	1	1	1	0	0	0	0	0	0
396	2	0	0	0	0	0	0	0	0
397	0	0	0	0	0	0	0	1	0
398	0	0	0	0	0	0	0	1	0
399	0	0	0	0	0	0	13	0	0
400	0	0	0	0	0	0	1	0	0
401	0	1	0	0	0	0	0	0	0
402	0	1	0	0	0	0	0	0	0
403	0	0	0	0	0	0	0	1	0
404	0	0	0	0	0	0	0	1	0
405	0	0	0	0	0	0	0	1	0
406	0	0	0	0	0	1	0	0	0
407	1	0	0	0	0	4	0	0	0
408	1	5	3	2	0	0	0	0	1
409	0	0	0	0	0	0	0	1	1
410	0	0	0	0	1	0	0	0	0
411	0	0	0	1	0	0	0	0	0
412	0	0	0	0	2	0	0	0	0
413	0	0	0	0	0	0	0	1	0
414	1	0	1	0	0	0	0	0	0
415	0	0	0	0	0	7	0	2	2
416	0	1	0	0	1	0	0	0	0"""

if __name__ =='__main__':
    main()
