# Copyright (c) 2018 luozhouyang
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from enum import IntEnum

from master_ai.core.similarity.cosine import Cosine
from master_ai.core.similarity.damerau import Damerau
from master_ai.core.similarity.jaccard import Jaccard
from master_ai.core.similarity.jarowinkler import JaroWinkler
from master_ai.core.similarity.levenshtein import Levenshtein
from master_ai.core.similarity.longest_common_subsequence import LongestCommonSubsequence
from master_ai.core.similarity.metric_lcs import MetricLCS
from master_ai.core.similarity.ngram import NGram
from master_ai.core.similarity.normalized_levenshtein import NormalizedLevenshtein
from master_ai.core.similarity.optimal_string_alignment import OptimalStringAlignment
from master_ai.core.similarity.qgram import QGram
from master_ai.core.similarity.sorensen_dice import SorensenDice
from master_ai.core.similarity.weighted_levenshtein import WeightedLevenshtein


class Algorithm(IntEnum):
    COSINE = 1
    DAMERAU = 2
    JACCARD = 3
    JARO_WINKLE = 4
    LEVENSHTEIN = 5
    LCS = 6
    METRIC_LCS = 7
    N_GRAM = 8
    NORMALIZED_LEVENSHTEIN = 9
    OPTIMAL_STRING_ALIGNMENT = 10
    Q_GRAM = 11
    SORENSEN_DICE = 12
    WEIGHTED_LEVENSHTEIN = 13


class Factory:
    @staticmethod
    def get_algorithm(algorithm: Algorithm, k=3):
        if algorithm == Algorithm.COSINE:
            return Cosine(k)
        elif algorithm == Algorithm.DAMERAU:
            return Damerau()
        elif algorithm == Algorithm.JACCARD:
            return Jaccard(k)
        elif algorithm == Algorithm.JARO_WINKLE:
            return JaroWinkler()
        elif algorithm == Algorithm.LEVENSHTEIN:
            return Levenshtein()
        elif algorithm == Algorithm.LCS:
            return LongestCommonSubsequence()
        elif algorithm == Algorithm.METRIC_LCS:
            return MetricLCS()
        elif algorithm == Algorithm.N_GRAM:
            return NGram()
        elif algorithm == Algorithm.NORMALIZED_LEVENSHTEIN:
            return NormalizedLevenshtein()
        elif algorithm == Algorithm.OPTIMAL_STRING_ALIGNMENT:
            return OptimalStringAlignment()
        elif algorithm == Algorithm.Q_GRAM:
            return QGram()
        elif algorithm == Algorithm.SORENSEN_DICE:
            return SorensenDice(k)
        elif algorithm == Algorithm.WEIGHTED_LEVENSHTEIN:
            raise TypeError("This method does not support create weighted_levenshtein algorithm.")
        else:
            return Cosine(k)

    @staticmethod
    def get_weighted_levenshtein(char_sub, char_change):
        return WeightedLevenshtein(char_sub, char_change)
#
# def read_text(text):
#     with open(text,"r") as f:
#         content = f.readlines()
#         content = "".join(content)
#         a  = content.replace("\n","")
#         a = a.replace("\u3000","")
#         return(a)
#
#
#
# a = Factory().get_algorithm(Algorithm.LEVENSHTEIN)
# temp1 = read_text("/Users/ruiliu/Desktop/333jpg.txt")
# temp2 = read_text("/Users/ruiliu/Desktop/HTZQYY0800_666810011960_00000354459088-1.txt")
# a.distance(temp1,temp2)
#
#
# text_path = "/Users/ruiliu/PycharmProjects/ocr_preprocess/text/"
#
# index = range(1,10)
# for i in index:
#         content_path = text_path + "IMG_260" + str(i) + ".txt"
#         origin_path = text_path + "IMG_260" + str(i) + "_origin.txt"
#         binary_path = text_path + "IMG_260" + str(i) + "_binary.txt"
#         small_path = text_path + "IMG_260" + str(i) + "_small.txt"
#         resize_path = text_path + "IMG_260" + str(i) + "_resize.txt"
#
#         content = read_text(content_path)
#         origin = read_text(origin_path)
#         binary = read_text(binary_path)
#         small = read_text(small_path)
#         resize = read_text(resize_path)
#
#         dis_origin = a.distance(content,origin)
#         dis_binary = a.distance(content, binary)
#         dis_resize = a.distance(content, resize)
#         dis_small = a.distance(content, small)
#
#
#         print("IMG_260",str(i),",", dis_origin, ",", dis_binary, ",", dis_resize, ",", dis_small)
#

