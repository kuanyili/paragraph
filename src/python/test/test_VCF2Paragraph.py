#!/usr/bin/env python3

# coding=utf-8
#
# Copyright (c) 2016-2019 Illumina, Inc.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied
# See the License for the specific language governing permissions and limitations
#
import os
import glob
import unittest
import subprocess
import tempfile
from pipes import quote

GRMPY_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))


class TestVCF2Paragraph(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = os.path.join(GRMPY_ROOT, "share", "test-data", "paragraph")
        self.test_haplo_vcfs = sorted(glob.glob(self.test_data_dir + "/simple/*.vcf"))
        self.test_haplo_vcfs = sorted(glob.glob(self.test_data_dir + "/haplo-complex/*.vcf"))
        self.test_haplo_vcfs += sorted(glob.glob(self.test_data_dir +
                                                 "/pg-het-ins/*.vcf"))
        self.test_haplo_vcfs += sorted(glob.glob(self.test_data_dir +
                                                 "/long-del/chr4-21369091-21376907.vcf"))

        self.test_allele_vcfs = sorted(glob.glob(self.test_data_dir + "/pg-complex/*.vcf"))
        self.test_allele_vcfs += sorted(glob.glob(os.path.join(GRMPY_ROOT, "share",
                                                               "test-data", "genotyping_test_2", "chr*.vcf")))

        self.test_insertion_vcfs = sorted(glob.glob(self.test_data_dir + "/insertions/*.vcf"))

        hg19_locations = [
            "/Users/pkrusche/workspace/human_genome/hg19.fa",
            "/illumina/sync/igenomes/Homo_sapiens/UCSC/hg19/Sequence/WholeGenomeFasta/genome.fa",
            "/Users/schen6/Documents/hg19/genome.fa"
        ]
        if "HG19" in os.environ and os.environ["HG19"]:
            hg19_locations.insert(0, os.environ["HG19"])
        self.hg19 = None
        for f in hg19_locations:
            if os.path.exists(f) and os.path.isfile(f):
                self.hg19 = f
                break

        if not self.hg19:
            raise Exception(
                "hg19 fasta file not found in expected locations: %s" % str(hg19_locations))

        hg38_locations = [
            "/Users/pkrusche/workspace/human_genome/hg38.fa",
            "/illumina/sync/igenomes/Homo_sapiens/NCBI/GRCh38Decoy/Sequence/WholeGenomeFasta/genome.fa",
        ]
        if "HG38" in os.environ and os.environ["HG38"]:
            hg38_locations.insert(0, os.environ["HG38"])
        self.hg38 = None
        for f in hg38_locations:
            if os.path.exists(f) and os.path.isfile(f):
                self.hg38 = f
                break

        if not self.hg38:
            raise Exception(
                "hg38 fasta file not found in expected locations: %s" % str(hg38_locations))

        self.vcf2paragraph = os.path.join(
            GRMPY_ROOT, "src", "python", "bin", "vcf2paragraph.py")

    def test_haplotype_vcfs(self):
        for x in self.test_haplo_vcfs:
            print("Testing output for %s..." % x)
            tf1 = tempfile.NamedTemporaryFile(suffix=".json")
            tf1.close()
            try:
                expected_json = x.replace(".vcf", ".json")
                subprocess.check_call(
                    f"python3 {quote(self.vcf2paragraph)} {quote(x)} {tf1.name} -r {self.hg19}",
                    shell=True)
                subprocess.check_call(
                    f"python3 -mjson.tool --sort-keys {tf1.name} > {tf1.name + '.pp.json'}",
                    shell=True)
                subprocess.check_call(
                    f"diff --ignore-matching-lines='.*model_name.*' {tf1.name + '.pp.json'} {expected_json}",
                    shell=True)
            except:
                from shutil import copy
                current_dir = os.path.abspath(os.path.dirname(__file__))
                basename = os.path.basename(expected_json)
                fail_path = os.path.join(current_dir, "test-failed-haplotype." + basename)
                copy(tf1.name + ".pp.json", fail_path)
                os.chmod(fail_path, 0o777)
                print("[test_haplotype_vcfs] failed output saved in %s" % fail_path)
                raise
            finally:
                os.remove(tf1.name)
                os.remove(tf1.name + ".pp.json")

    def test_allele_graph_vcfs(self):
        for x in self.test_allele_vcfs:
            print("Testing output for %s..." % x)
            tf1 = tempfile.NamedTemporaryFile(suffix=".json")
            tf1.close()
            try:
                if "genotyping_test_2" in x:
                    reference = os.path.join(GRMPY_ROOT, "share", "test-data", "genotyping_test_2", "swaps.fa")
                else:
                    reference = self.hg38
                expected_json = x.replace(".vcf", ".json")
                subprocess.check_call("python3 %s %s %s -r %s -R -g alleles" % (
                    quote(self.vcf2paragraph), quote(x), tf1.name, reference
                ), shell=True)
                subprocess.check_call(
                    "python3 -mjson.tool --sort-keys %s > %s" % (tf1.name, tf1.name + ".pp.json"),
                    shell=True)
                subprocess.check_call("diff --ignore-matching-lines='.*model_name.*' %s %s" %
                                      (tf1.name + ".pp.json", expected_json),
                                      shell=True)
            except:  # pylint: disable=bare-except
                from shutil import copy
                current_dir = os.path.abspath(os.path.dirname(__file__))
                basename = os.path.basename(expected_json)
                failed_path = os.path.join(current_dir, "test-failed-allele." + basename)
                copy(tf1.name + ".pp.json", failed_path)
                os.chmod(failed_path, 0o777)
                print("[test_allele_graph_vcfs] Failed output saved in %s" % failed_path)
                raise
            finally:
                os.remove(tf1.name)
                os.remove(tf1.name + ".pp.json")

    def test_allele_graph_insertion_vcfs(self):
        assert self.test_insertion_vcfs
        for x in self.test_insertion_vcfs:
            print("Testing output for %s..." % x)
            tf1 = tempfile.NamedTemporaryFile(suffix=".json")
            tf1.close()
            try:
                expected_json = x.replace(".vcf", ".json")
                reference = x.replace(".vcf", ".ref.fa")
                # check with allele splitting
                subprocess.check_call("python3 %s %s %s -r %s --alt-splitting "
                                      "--read-len 5 --max-ref-node-length 10 --alt-paths "
                                      "--retrieve-reference-sequence -g alleles" % (
                                          quote(self.vcf2paragraph), quote(x), tf1.name, reference
                                      ), shell=True)
                subprocess.check_call(
                    "python3 -mjson.tool --sort-keys %s > %s" % (tf1.name, tf1.name + ".pp.json"),
                    shell=True)
                subprocess.check_call("diff --ignore-matching-lines='.*model_name.*' %s %s" %
                                      (tf1.name + ".pp.json", expected_json),
                                      shell=True)

                # check without alt splitting
                expected_json = x.replace(".vcf", ".noas.json")
                subprocess.check_call("python3 %s %s %s -r %s "
                                      "--read-len 5 --max-ref-node-length 10 --alt-paths "
                                      "--retrieve-reference-sequence -g alleles" % (
                                          quote(self.vcf2paragraph), quote(x), tf1.name, reference
                                      ), shell=True)
                subprocess.check_call(
                    "python3 -mjson.tool --sort-keys %s > %s" % (tf1.name, tf1.name + ".pp.json"),
                    shell=True)
                subprocess.check_call("diff --ignore-matching-lines='.*model_name.*' %s %s" %
                                      (tf1.name + ".pp.json", expected_json),
                                      shell=True)
            except:  # pylint: disable=bare-except
                from shutil import copy
                current_dir = os.path.abspath(os.path.dirname(__file__))
                basename = os.path.basename(expected_json)
                failed_path = os.path.join(current_dir, "test-failed-allele-ins." + basename)
                copy(tf1.name + ".pp.json", failed_path)
                os.chmod(failed_path, 0o777)
                print("Failed output saved in %s" % failed_path)
                raise
            finally:
                os.remove(tf1.name)
                os.remove(tf1.name + ".pp.json")


if __name__ == "__main__":
    unittest.main()
