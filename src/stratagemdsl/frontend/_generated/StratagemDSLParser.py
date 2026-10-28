# Generated from src/stratagemdsl/frontend/grammar/StratagemDSL.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,76,708,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,2,33,
        7,33,2,34,7,34,2,35,7,35,2,36,7,36,2,37,7,37,2,38,7,38,2,39,7,39,
        2,40,7,40,2,41,7,41,2,42,7,42,2,43,7,43,2,44,7,44,2,45,7,45,2,46,
        7,46,2,47,7,47,2,48,7,48,2,49,7,49,2,50,7,50,2,51,7,51,2,52,7,52,
        2,53,7,53,2,54,7,54,2,55,7,55,2,56,7,56,2,57,7,57,2,58,7,58,2,59,
        7,59,2,60,7,60,2,61,7,61,2,62,7,62,2,63,7,63,2,64,7,64,1,0,1,0,1,
        0,1,1,1,1,1,1,1,1,1,1,3,1,139,8,1,1,1,1,1,3,1,143,8,1,1,1,1,1,3,
        1,147,8,1,1,1,1,1,1,2,1,2,1,2,5,2,154,8,2,10,2,12,2,157,9,2,1,2,
        1,2,1,3,1,3,1,3,3,3,164,8,3,1,3,3,3,167,8,3,1,3,1,3,1,3,3,3,172,
        8,3,1,3,3,3,175,8,3,1,3,1,3,1,3,3,3,180,8,3,1,3,3,3,183,8,3,1,3,
        1,3,1,3,3,3,188,8,3,1,3,3,3,191,8,3,3,3,193,8,3,1,4,1,4,5,4,197,
        8,4,10,4,12,4,200,9,4,1,4,1,4,1,5,1,5,1,5,1,5,1,5,1,6,1,6,1,6,1,
        6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,3,6,222,8,6,1,7,1,7,1,8,1,
        8,1,8,1,8,5,8,230,8,8,10,8,12,8,233,9,8,3,8,235,8,8,1,8,1,8,1,9,
        1,9,1,9,5,9,242,8,9,10,9,12,9,245,9,9,1,9,1,9,1,10,1,10,1,10,1,11,
        1,11,1,11,3,11,255,8,11,1,11,1,11,3,11,259,8,11,1,11,1,11,1,11,1,
        11,1,12,1,12,1,12,1,12,1,12,1,12,1,12,5,12,272,8,12,10,12,12,12,
        275,9,12,1,12,3,12,278,8,12,1,13,1,13,1,13,1,13,1,13,1,14,1,14,1,
        14,1,14,1,15,1,15,1,15,1,15,1,16,1,16,1,16,1,16,1,17,1,17,1,17,1,
        17,1,18,1,18,1,18,5,18,304,8,18,10,18,12,18,307,9,18,1,18,1,18,1,
        19,1,19,1,19,1,19,1,19,1,19,1,20,1,20,1,20,1,20,4,20,321,8,20,11,
        20,12,20,322,1,20,5,20,326,8,20,10,20,12,20,329,9,20,1,20,1,20,1,
        21,1,21,1,21,1,21,1,22,1,22,1,22,3,22,340,8,22,1,23,1,23,1,23,1,
        23,1,23,3,23,347,8,23,1,23,3,23,350,8,23,1,23,3,23,353,8,23,1,23,
        3,23,356,8,23,1,23,3,23,359,8,23,1,23,3,23,362,8,23,1,23,3,23,365,
        8,23,1,23,3,23,368,8,23,1,23,1,23,1,24,1,24,1,24,1,24,1,25,1,25,
        1,25,1,26,1,26,1,26,1,26,1,27,1,27,1,27,1,27,1,28,1,28,1,28,1,28,
        1,29,1,29,1,29,1,30,1,30,1,30,1,30,1,31,1,31,1,31,1,31,1,32,1,32,
        1,32,1,32,1,33,1,33,3,33,408,8,33,1,34,1,34,1,34,1,34,1,34,1,35,
        1,35,1,35,1,35,1,35,1,35,3,35,421,8,35,1,36,1,36,1,36,1,36,3,36,
        427,8,36,1,36,3,36,430,8,36,1,36,3,36,433,8,36,1,36,1,36,1,37,1,
        37,1,37,1,37,1,38,1,38,1,38,1,38,1,39,1,39,1,39,1,39,1,39,1,39,1,
        39,1,39,3,39,453,8,39,1,39,3,39,456,8,39,1,39,3,39,459,8,39,1,39,
        1,39,1,39,1,39,1,39,1,40,1,40,1,40,5,40,469,8,40,10,40,12,40,472,
        9,40,1,41,1,41,1,41,1,41,1,41,1,41,1,41,1,41,1,41,1,41,1,41,1,41,
        1,41,1,41,1,41,1,41,3,41,490,8,41,1,42,1,42,1,42,1,42,1,43,1,43,
        1,43,1,43,1,44,1,44,5,44,502,8,44,10,44,12,44,505,9,44,1,44,1,44,
        1,44,1,44,5,44,511,8,44,10,44,12,44,514,9,44,1,44,1,44,1,44,1,44,
        5,44,520,8,44,10,44,12,44,523,9,44,1,44,3,44,526,8,44,1,45,1,45,
        1,45,1,46,1,46,1,46,1,46,5,46,535,8,46,10,46,12,46,538,9,46,3,46,
        540,8,46,1,46,1,46,1,47,1,47,1,47,1,47,5,47,548,8,47,10,47,12,47,
        551,9,47,1,47,1,47,1,48,1,48,1,48,1,48,1,48,1,49,1,49,1,49,3,49,
        563,8,49,1,49,1,49,1,49,1,49,1,49,1,49,1,49,1,49,1,49,1,49,1,49,
        1,49,1,49,1,49,1,49,1,49,1,49,1,49,5,49,583,8,49,10,49,12,49,586,
        9,49,3,49,588,8,49,1,49,3,49,591,8,49,1,50,1,50,1,50,5,50,596,8,
        50,10,50,12,50,599,9,50,1,51,1,51,1,51,1,51,1,51,3,51,606,8,51,1,
        52,1,52,1,53,1,53,1,54,1,54,1,54,1,54,1,54,3,54,617,8,54,1,55,1,
        55,1,55,1,55,1,55,1,55,5,55,625,8,55,10,55,12,55,628,9,55,1,56,1,
        56,1,56,1,56,1,56,1,56,5,56,636,8,56,10,56,12,56,639,9,56,1,57,1,
        57,1,57,1,57,1,57,3,57,646,8,57,1,58,1,58,1,58,1,58,1,58,1,58,5,
        58,654,8,58,10,58,12,58,657,9,58,1,59,1,59,1,59,1,59,1,59,1,59,5,
        59,665,8,59,10,59,12,59,668,9,59,1,60,1,60,1,60,1,60,1,60,3,60,675,
        8,60,1,61,1,61,1,61,1,61,1,61,1,61,1,61,3,61,684,8,61,1,62,1,62,
        1,62,3,62,689,8,62,1,62,1,62,1,63,1,63,1,63,5,63,696,8,63,10,63,
        12,63,699,9,63,1,64,1,64,1,64,1,64,1,64,3,64,706,8,64,1,64,0,4,110,
        112,116,118,65,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,
        36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,66,68,70,72,74,76,78,
        80,82,84,86,88,90,92,94,96,98,100,102,104,106,108,110,112,114,116,
        118,120,122,124,126,128,0,5,2,0,1,40,73,73,2,0,15,15,73,73,2,0,53,
        54,56,59,1,0,60,61,1,0,62,63,740,0,130,1,0,0,0,2,133,1,0,0,0,4,150,
        1,0,0,0,6,192,1,0,0,0,8,194,1,0,0,0,10,203,1,0,0,0,12,221,1,0,0,
        0,14,223,1,0,0,0,16,225,1,0,0,0,18,238,1,0,0,0,20,248,1,0,0,0,22,
        251,1,0,0,0,24,277,1,0,0,0,26,279,1,0,0,0,28,284,1,0,0,0,30,288,
        1,0,0,0,32,292,1,0,0,0,34,296,1,0,0,0,36,300,1,0,0,0,38,310,1,0,
        0,0,40,316,1,0,0,0,42,332,1,0,0,0,44,339,1,0,0,0,46,341,1,0,0,0,
        48,371,1,0,0,0,50,375,1,0,0,0,52,378,1,0,0,0,54,382,1,0,0,0,56,386,
        1,0,0,0,58,390,1,0,0,0,60,393,1,0,0,0,62,397,1,0,0,0,64,401,1,0,
        0,0,66,407,1,0,0,0,68,409,1,0,0,0,70,420,1,0,0,0,72,422,1,0,0,0,
        74,436,1,0,0,0,76,440,1,0,0,0,78,444,1,0,0,0,80,465,1,0,0,0,82,489,
        1,0,0,0,84,491,1,0,0,0,86,495,1,0,0,0,88,525,1,0,0,0,90,527,1,0,
        0,0,92,530,1,0,0,0,94,543,1,0,0,0,96,554,1,0,0,0,98,590,1,0,0,0,
        100,592,1,0,0,0,102,605,1,0,0,0,104,607,1,0,0,0,106,609,1,0,0,0,
        108,616,1,0,0,0,110,618,1,0,0,0,112,629,1,0,0,0,114,645,1,0,0,0,
        116,647,1,0,0,0,118,658,1,0,0,0,120,674,1,0,0,0,122,683,1,0,0,0,
        124,685,1,0,0,0,126,692,1,0,0,0,128,705,1,0,0,0,130,131,3,2,1,0,
        131,132,5,0,0,1,132,1,1,0,0,0,133,134,5,1,0,0,134,135,5,73,0,0,135,
        136,5,64,0,0,136,138,3,4,2,0,137,139,3,18,9,0,138,137,1,0,0,0,138,
        139,1,0,0,0,139,140,1,0,0,0,140,142,3,22,11,0,141,143,3,36,18,0,
        142,141,1,0,0,0,142,143,1,0,0,0,143,144,1,0,0,0,144,146,3,40,20,
        0,145,147,3,94,47,0,146,145,1,0,0,0,146,147,1,0,0,0,147,148,1,0,
        0,0,148,149,5,65,0,0,149,3,1,0,0,0,150,151,5,2,0,0,151,155,5,64,
        0,0,152,154,3,6,3,0,153,152,1,0,0,0,154,157,1,0,0,0,155,153,1,0,
        0,0,155,156,1,0,0,0,156,158,1,0,0,0,157,155,1,0,0,0,158,159,5,65,
        0,0,159,5,1,0,0,0,160,161,5,12,0,0,161,163,5,73,0,0,162,164,3,8,
        4,0,163,162,1,0,0,0,163,164,1,0,0,0,164,166,1,0,0,0,165,167,5,50,
        0,0,166,165,1,0,0,0,166,167,1,0,0,0,167,193,1,0,0,0,168,169,5,13,
        0,0,169,171,5,73,0,0,170,172,3,8,4,0,171,170,1,0,0,0,171,172,1,0,
        0,0,172,174,1,0,0,0,173,175,5,50,0,0,174,173,1,0,0,0,174,175,1,0,
        0,0,175,193,1,0,0,0,176,177,5,14,0,0,177,179,5,73,0,0,178,180,3,
        8,4,0,179,178,1,0,0,0,179,180,1,0,0,0,180,182,1,0,0,0,181,183,5,
        50,0,0,182,181,1,0,0,0,182,183,1,0,0,0,183,193,1,0,0,0,184,185,5,
        15,0,0,185,187,5,73,0,0,186,188,3,8,4,0,187,186,1,0,0,0,187,188,
        1,0,0,0,188,190,1,0,0,0,189,191,5,50,0,0,190,189,1,0,0,0,190,191,
        1,0,0,0,191,193,1,0,0,0,192,160,1,0,0,0,192,168,1,0,0,0,192,176,
        1,0,0,0,192,184,1,0,0,0,193,7,1,0,0,0,194,198,5,64,0,0,195,197,3,
        10,5,0,196,195,1,0,0,0,197,200,1,0,0,0,198,196,1,0,0,0,198,199,1,
        0,0,0,199,201,1,0,0,0,200,198,1,0,0,0,201,202,5,65,0,0,202,9,1,0,
        0,0,203,204,3,14,7,0,204,205,5,52,0,0,205,206,3,12,6,0,206,207,5,
        50,0,0,207,11,1,0,0,0,208,222,5,72,0,0,209,222,5,70,0,0,210,222,
        5,71,0,0,211,212,5,61,0,0,212,213,5,70,0,0,213,222,4,6,0,1,214,215,
        5,61,0,0,215,216,5,71,0,0,216,222,4,6,1,1,217,222,5,41,0,0,218,222,
        5,42,0,0,219,222,3,14,7,0,220,222,3,16,8,0,221,208,1,0,0,0,221,209,
        1,0,0,0,221,210,1,0,0,0,221,211,1,0,0,0,221,214,1,0,0,0,221,217,
        1,0,0,0,221,218,1,0,0,0,221,219,1,0,0,0,221,220,1,0,0,0,222,13,1,
        0,0,0,223,224,7,0,0,0,224,15,1,0,0,0,225,234,5,66,0,0,226,231,3,
        12,6,0,227,228,5,51,0,0,228,230,3,12,6,0,229,227,1,0,0,0,230,233,
        1,0,0,0,231,229,1,0,0,0,231,232,1,0,0,0,232,235,1,0,0,0,233,231,
        1,0,0,0,234,226,1,0,0,0,234,235,1,0,0,0,235,236,1,0,0,0,236,237,
        5,67,0,0,237,17,1,0,0,0,238,239,5,3,0,0,239,243,5,64,0,0,240,242,
        3,20,10,0,241,240,1,0,0,0,242,245,1,0,0,0,243,241,1,0,0,0,243,244,
        1,0,0,0,244,246,1,0,0,0,245,243,1,0,0,0,246,247,5,65,0,0,247,19,
        1,0,0,0,248,249,3,106,53,0,249,250,5,50,0,0,250,21,1,0,0,0,251,252,
        5,4,0,0,252,254,5,64,0,0,253,255,3,24,12,0,254,253,1,0,0,0,254,255,
        1,0,0,0,255,256,1,0,0,0,256,258,3,28,14,0,257,259,3,30,15,0,258,
        257,1,0,0,0,258,259,1,0,0,0,259,260,1,0,0,0,260,261,3,32,16,0,261,
        262,3,34,17,0,262,263,5,65,0,0,263,23,1,0,0,0,264,265,5,7,0,0,265,
        266,5,73,0,0,266,278,5,50,0,0,267,268,5,7,0,0,268,269,5,73,0,0,269,
        273,5,64,0,0,270,272,3,26,13,0,271,270,1,0,0,0,272,275,1,0,0,0,273,
        271,1,0,0,0,273,274,1,0,0,0,274,276,1,0,0,0,275,273,1,0,0,0,276,
        278,5,65,0,0,277,264,1,0,0,0,277,267,1,0,0,0,278,25,1,0,0,0,279,
        280,5,73,0,0,280,281,5,52,0,0,281,282,5,73,0,0,282,283,5,50,0,0,
        283,27,1,0,0,0,284,285,5,8,0,0,285,286,3,106,53,0,286,287,5,50,0,
        0,287,29,1,0,0,0,288,289,5,9,0,0,289,290,3,106,53,0,290,291,5,50,
        0,0,291,31,1,0,0,0,292,293,5,10,0,0,293,294,3,106,53,0,294,295,5,
        50,0,0,295,33,1,0,0,0,296,297,5,11,0,0,297,298,3,106,53,0,298,299,
        5,50,0,0,299,35,1,0,0,0,300,301,5,5,0,0,301,305,5,64,0,0,302,304,
        3,38,19,0,303,302,1,0,0,0,304,307,1,0,0,0,305,303,1,0,0,0,305,306,
        1,0,0,0,306,308,1,0,0,0,307,305,1,0,0,0,308,309,5,65,0,0,309,37,
        1,0,0,0,310,311,5,6,0,0,311,312,5,73,0,0,312,313,5,52,0,0,313,314,
        3,106,53,0,314,315,5,50,0,0,315,39,1,0,0,0,316,317,5,16,0,0,317,
        318,5,64,0,0,318,320,3,42,21,0,319,321,3,44,22,0,320,319,1,0,0,0,
        321,322,1,0,0,0,322,320,1,0,0,0,322,323,1,0,0,0,323,327,1,0,0,0,
        324,326,3,78,39,0,325,324,1,0,0,0,326,329,1,0,0,0,327,325,1,0,0,
        0,327,328,1,0,0,0,328,330,1,0,0,0,329,327,1,0,0,0,330,331,5,65,0,
        0,331,41,1,0,0,0,332,333,5,17,0,0,333,334,3,92,46,0,334,335,5,50,
        0,0,335,43,1,0,0,0,336,340,3,46,23,0,337,340,3,68,34,0,338,340,3,
        72,36,0,339,336,1,0,0,0,339,337,1,0,0,0,339,338,1,0,0,0,340,45,1,
        0,0,0,341,342,5,18,0,0,342,343,5,73,0,0,343,344,5,64,0,0,344,346,
        3,48,24,0,345,347,3,50,25,0,346,345,1,0,0,0,346,347,1,0,0,0,347,
        349,1,0,0,0,348,350,3,52,26,0,349,348,1,0,0,0,349,350,1,0,0,0,350,
        352,1,0,0,0,351,353,3,54,27,0,352,351,1,0,0,0,352,353,1,0,0,0,353,
        355,1,0,0,0,354,356,3,56,28,0,355,354,1,0,0,0,355,356,1,0,0,0,356,
        358,1,0,0,0,357,359,3,58,29,0,358,357,1,0,0,0,358,359,1,0,0,0,359,
        361,1,0,0,0,360,362,3,60,30,0,361,360,1,0,0,0,361,362,1,0,0,0,362,
        364,1,0,0,0,363,365,3,62,31,0,364,363,1,0,0,0,364,365,1,0,0,0,365,
        367,1,0,0,0,366,368,3,64,32,0,367,366,1,0,0,0,367,368,1,0,0,0,368,
        369,1,0,0,0,369,370,5,65,0,0,370,47,1,0,0,0,371,372,5,20,0,0,372,
        373,5,72,0,0,373,374,5,50,0,0,374,49,1,0,0,0,375,376,5,40,0,0,376,
        377,5,50,0,0,377,51,1,0,0,0,378,379,5,21,0,0,379,380,3,92,46,0,380,
        381,5,50,0,0,381,53,1,0,0,0,382,383,5,22,0,0,383,384,3,92,46,0,384,
        385,5,50,0,0,385,55,1,0,0,0,386,387,5,23,0,0,387,388,3,106,53,0,
        388,389,5,50,0,0,389,57,1,0,0,0,390,391,5,24,0,0,391,392,3,88,44,
        0,392,59,1,0,0,0,393,394,5,25,0,0,394,395,3,106,53,0,395,396,5,50,
        0,0,396,61,1,0,0,0,397,398,5,26,0,0,398,399,3,106,53,0,399,400,5,
        50,0,0,400,63,1,0,0,0,401,402,5,27,0,0,402,403,3,66,33,0,403,404,
        5,50,0,0,404,65,1,0,0,0,405,408,5,10,0,0,406,408,5,11,0,0,407,405,
        1,0,0,0,407,406,1,0,0,0,408,67,1,0,0,0,409,410,5,19,0,0,410,411,
        5,73,0,0,411,412,3,70,35,0,412,413,5,50,0,0,413,69,1,0,0,0,414,421,
        5,32,0,0,415,421,5,33,0,0,416,417,5,34,0,0,417,418,5,68,0,0,418,
        419,5,70,0,0,419,421,5,69,0,0,420,414,1,0,0,0,420,415,1,0,0,0,420,
        416,1,0,0,0,421,71,1,0,0,0,422,423,5,38,0,0,423,424,5,73,0,0,424,
        426,5,64,0,0,425,427,3,48,24,0,426,425,1,0,0,0,426,427,1,0,0,0,427,
        429,1,0,0,0,428,430,3,74,37,0,429,428,1,0,0,0,429,430,1,0,0,0,430,
        432,1,0,0,0,431,433,3,76,38,0,432,431,1,0,0,0,432,433,1,0,0,0,433,
        434,1,0,0,0,434,435,5,65,0,0,435,73,1,0,0,0,436,437,5,3,0,0,437,
        438,5,70,0,0,438,439,5,50,0,0,439,75,1,0,0,0,440,441,5,39,0,0,441,
        442,5,70,0,0,442,443,5,50,0,0,443,77,1,0,0,0,444,445,5,28,0,0,445,
        446,5,73,0,0,446,447,5,49,0,0,447,448,3,80,40,0,448,449,5,47,0,0,
        449,450,3,80,40,0,450,452,5,64,0,0,451,453,3,84,42,0,452,451,1,0,
        0,0,452,453,1,0,0,0,453,455,1,0,0,0,454,456,3,86,43,0,455,454,1,
        0,0,0,455,456,1,0,0,0,456,458,1,0,0,0,457,459,3,58,29,0,458,457,
        1,0,0,0,458,459,1,0,0,0,459,460,1,0,0,0,460,461,5,31,0,0,461,462,
        5,70,0,0,462,463,5,50,0,0,463,464,5,65,0,0,464,79,1,0,0,0,465,470,
        3,82,41,0,466,467,5,51,0,0,467,469,3,82,41,0,468,466,1,0,0,0,469,
        472,1,0,0,0,470,468,1,0,0,0,470,471,1,0,0,0,471,81,1,0,0,0,472,470,
        1,0,0,0,473,490,5,73,0,0,474,475,5,73,0,0,475,476,5,62,0,0,476,490,
        5,70,0,0,477,478,5,48,0,0,478,490,5,73,0,0,479,480,5,48,0,0,480,
        481,5,73,0,0,481,482,5,62,0,0,482,490,5,70,0,0,483,484,5,55,0,0,
        484,490,5,73,0,0,485,486,5,55,0,0,486,487,5,73,0,0,487,488,5,62,
        0,0,488,490,5,70,0,0,489,473,1,0,0,0,489,474,1,0,0,0,489,477,1,0,
        0,0,489,479,1,0,0,0,489,483,1,0,0,0,489,485,1,0,0,0,490,83,1,0,0,
        0,491,492,5,29,0,0,492,493,3,124,62,0,493,494,5,50,0,0,494,85,1,
        0,0,0,495,496,5,30,0,0,496,497,3,106,53,0,497,498,5,50,0,0,498,87,
        1,0,0,0,499,503,5,64,0,0,500,502,3,90,45,0,501,500,1,0,0,0,502,505,
        1,0,0,0,503,501,1,0,0,0,503,504,1,0,0,0,504,506,1,0,0,0,505,503,
        1,0,0,0,506,526,5,65,0,0,507,508,5,35,0,0,508,512,5,64,0,0,509,511,
        3,90,45,0,510,509,1,0,0,0,511,514,1,0,0,0,512,510,1,0,0,0,512,513,
        1,0,0,0,513,515,1,0,0,0,514,512,1,0,0,0,515,526,5,65,0,0,516,517,
        5,36,0,0,517,521,5,64,0,0,518,520,3,90,45,0,519,518,1,0,0,0,520,
        523,1,0,0,0,521,519,1,0,0,0,521,522,1,0,0,0,522,524,1,0,0,0,523,
        521,1,0,0,0,524,526,5,65,0,0,525,499,1,0,0,0,525,507,1,0,0,0,525,
        516,1,0,0,0,526,89,1,0,0,0,527,528,3,124,62,0,528,529,5,50,0,0,529,
        91,1,0,0,0,530,539,5,66,0,0,531,536,5,73,0,0,532,533,5,51,0,0,533,
        535,5,73,0,0,534,532,1,0,0,0,535,538,1,0,0,0,536,534,1,0,0,0,536,
        537,1,0,0,0,537,540,1,0,0,0,538,536,1,0,0,0,539,531,1,0,0,0,539,
        540,1,0,0,0,540,541,1,0,0,0,541,542,5,67,0,0,542,93,1,0,0,0,543,
        544,5,37,0,0,544,545,5,73,0,0,545,549,5,64,0,0,546,548,3,96,48,0,
        547,546,1,0,0,0,548,551,1,0,0,0,549,547,1,0,0,0,549,550,1,0,0,0,
        550,552,1,0,0,0,551,549,1,0,0,0,552,553,5,65,0,0,553,95,1,0,0,0,
        554,555,5,73,0,0,555,556,5,52,0,0,556,557,3,98,49,0,557,558,5,50,
        0,0,558,97,1,0,0,0,559,560,3,104,52,0,560,562,5,68,0,0,561,563,3,
        100,50,0,562,561,1,0,0,0,562,563,1,0,0,0,563,564,1,0,0,0,564,565,
        5,69,0,0,565,591,1,0,0,0,566,591,5,72,0,0,567,591,5,70,0,0,568,591,
        5,71,0,0,569,570,5,61,0,0,570,571,5,70,0,0,571,591,4,49,2,1,572,
        573,5,61,0,0,573,574,5,71,0,0,574,591,4,49,3,1,575,591,5,41,0,0,
        576,591,5,42,0,0,577,591,3,14,7,0,578,587,5,66,0,0,579,584,3,98,
        49,0,580,581,5,51,0,0,581,583,3,98,49,0,582,580,1,0,0,0,583,586,
        1,0,0,0,584,582,1,0,0,0,584,585,1,0,0,0,585,588,1,0,0,0,586,584,
        1,0,0,0,587,579,1,0,0,0,587,588,1,0,0,0,588,589,1,0,0,0,589,591,
        5,67,0,0,590,559,1,0,0,0,590,566,1,0,0,0,590,567,1,0,0,0,590,568,
        1,0,0,0,590,569,1,0,0,0,590,572,1,0,0,0,590,575,1,0,0,0,590,576,
        1,0,0,0,590,577,1,0,0,0,590,578,1,0,0,0,591,99,1,0,0,0,592,597,3,
        102,51,0,593,594,5,51,0,0,594,596,3,102,51,0,595,593,1,0,0,0,596,
        599,1,0,0,0,597,595,1,0,0,0,597,598,1,0,0,0,598,101,1,0,0,0,599,
        597,1,0,0,0,600,601,3,14,7,0,601,602,5,52,0,0,602,603,3,98,49,0,
        603,606,1,0,0,0,604,606,3,98,49,0,605,600,1,0,0,0,605,604,1,0,0,
        0,606,103,1,0,0,0,607,608,7,1,0,0,608,105,1,0,0,0,609,610,3,108,
        54,0,610,107,1,0,0,0,611,617,3,110,55,0,612,613,3,110,55,0,613,614,
        5,46,0,0,614,615,3,108,54,0,615,617,1,0,0,0,616,611,1,0,0,0,616,
        612,1,0,0,0,617,109,1,0,0,0,618,619,6,55,-1,0,619,620,3,112,56,0,
        620,626,1,0,0,0,621,622,10,1,0,0,622,623,5,45,0,0,623,625,3,112,
        56,0,624,621,1,0,0,0,625,628,1,0,0,0,626,624,1,0,0,0,626,627,1,0,
        0,0,627,111,1,0,0,0,628,626,1,0,0,0,629,630,6,56,-1,0,630,631,3,
        114,57,0,631,637,1,0,0,0,632,633,10,1,0,0,633,634,5,44,0,0,634,636,
        3,114,57,0,635,632,1,0,0,0,636,639,1,0,0,0,637,635,1,0,0,0,637,638,
        1,0,0,0,638,113,1,0,0,0,639,637,1,0,0,0,640,646,3,116,58,0,641,642,
        3,116,58,0,642,643,7,2,0,0,643,644,3,116,58,0,644,646,1,0,0,0,645,
        640,1,0,0,0,645,641,1,0,0,0,646,115,1,0,0,0,647,648,6,58,-1,0,648,
        649,3,118,59,0,649,655,1,0,0,0,650,651,10,1,0,0,651,652,7,3,0,0,
        652,654,3,118,59,0,653,650,1,0,0,0,654,657,1,0,0,0,655,653,1,0,0,
        0,655,656,1,0,0,0,656,117,1,0,0,0,657,655,1,0,0,0,658,659,6,59,-1,
        0,659,660,3,120,60,0,660,666,1,0,0,0,661,662,10,1,0,0,662,663,7,
        4,0,0,663,665,3,120,60,0,664,661,1,0,0,0,665,668,1,0,0,0,666,664,
        1,0,0,0,666,667,1,0,0,0,667,119,1,0,0,0,668,666,1,0,0,0,669,670,
        5,43,0,0,670,675,3,120,60,0,671,672,5,61,0,0,672,675,3,120,60,0,
        673,675,3,122,61,0,674,669,1,0,0,0,674,671,1,0,0,0,674,673,1,0,0,
        0,675,121,1,0,0,0,676,677,5,68,0,0,677,678,3,106,53,0,678,679,5,
        69,0,0,679,684,1,0,0,0,680,684,3,124,62,0,681,684,3,128,64,0,682,
        684,5,73,0,0,683,676,1,0,0,0,683,680,1,0,0,0,683,681,1,0,0,0,683,
        682,1,0,0,0,684,123,1,0,0,0,685,686,5,73,0,0,686,688,5,68,0,0,687,
        689,3,126,63,0,688,687,1,0,0,0,688,689,1,0,0,0,689,690,1,0,0,0,690,
        691,5,69,0,0,691,125,1,0,0,0,692,697,3,106,53,0,693,694,5,51,0,0,
        694,696,3,106,53,0,695,693,1,0,0,0,696,699,1,0,0,0,697,695,1,0,0,
        0,697,698,1,0,0,0,698,127,1,0,0,0,699,697,1,0,0,0,700,706,5,72,0,
        0,701,706,5,70,0,0,702,706,5,71,0,0,703,706,5,41,0,0,704,706,5,42,
        0,0,705,700,1,0,0,0,705,701,1,0,0,0,705,702,1,0,0,0,705,703,1,0,
        0,0,705,704,1,0,0,0,706,129,1,0,0,0,68,138,142,146,155,163,166,171,
        174,179,182,187,190,192,198,221,231,234,243,254,258,273,277,305,
        322,327,339,346,349,352,355,358,361,364,367,407,420,426,429,432,
        452,455,458,470,489,503,512,521,525,536,539,549,562,584,587,590,
        597,605,616,626,637,645,655,666,674,683,688,697,705
    ]

class StratagemDSLParser ( Parser ):

    grammarFileName = "StratagemDSL.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'strategy'", "'world'", "'initial'", 
                     "'intent'", "'semantics'", "'derive'", "'pattern'", 
                     "'primary'", "'secondary'", "'success'", "'failure'", 
                     "'force'", "'asset'", "'region'", "'route'", "'plan'", 
                     "'start'", "'phase'", "'join'", "'purpose'", "'actors'", 
                     "'focus'", "'entry'", "'do'", "'invariant'", "'exit'", 
                     "'terminal'", "'transition'", "'on'", "'when'", "'priority'", 
                     "'all'", "'any'", "'atleast'", "'sequence'", "'parallel'", 
                     "'binding'", "'place'", "'capacity'", "'repeatable'", 
                     "'true'", "'false'", "'not'", "'and'", "'or'", "'implies'", 
                     "'->'", "'?'", "':'", "';'", "','", "'='", "'=='", 
                     "'!='", "'!'", "'<='", "'>='", "'<'", "'>'", "'+'", 
                     "'-'", "'*'", "'/'", "'{'", "'}'", "'['", "']'", "'('", 
                     "')'" ]

    symbolicNames = [ "<INVALID>", "STRATEGY", "WORLD", "INITIAL", "INTENT", 
                      "SEMANTICS", "DERIVE", "PATTERN", "PRIMARY", "SECONDARY", 
                      "SUCCESS", "FAILURE", "FORCE", "ASSET", "REGION", 
                      "ROUTE", "PLAN", "START", "PHASE", "JOIN", "PURPOSE", 
                      "ACTORS", "FOCUS", "ENTRY", "DO", "INVARIANT", "EXIT", 
                      "TERMINAL", "TRANSITION", "ON", "WHEN", "PRIORITY", 
                      "ALL", "ANY", "ATLEAST", "SEQUENCE", "PARALLEL", "BINDING", 
                      "PLACE", "CAPACITY", "REPEATABLE", "TRUE", "FALSE", 
                      "NOT", "AND", "OR", "IMPLIES", "ARROW", "QMARK", "COLON", 
                      "SEMI", "COMMA", "ASSIGN", "EQ", "NEQ", "BANG", "LE", 
                      "GE", "LT", "GT", "PLUS", "MINUS", "MUL", "DIV", "LBRACE", 
                      "RBRACE", "LBRACK", "RBRACK", "LPAREN", "RPAREN", 
                      "INT", "NUMBER", "STRING", "ID", "COMMENT", "BLOCK_COMMENT", 
                      "WS" ]

    RULE_document = 0
    RULE_strategyDecl = 1
    RULE_worldSection = 2
    RULE_entityDecl = 3
    RULE_entityBody = 4
    RULE_propertyStmt = 5
    RULE_propertyValue = 6
    RULE_softId = 7
    RULE_listValue = 8
    RULE_initialSection = 9
    RULE_exprStmt = 10
    RULE_intentSection = 11
    RULE_patternStmt = 12
    RULE_patternRoleBinding = 13
    RULE_primaryStmt = 14
    RULE_secondaryStmt = 15
    RULE_successStmt = 16
    RULE_failureStmt = 17
    RULE_semanticsSection = 18
    RULE_derivedDecl = 19
    RULE_planSection = 20
    RULE_startStmt = 21
    RULE_planNode = 22
    RULE_phaseDecl = 23
    RULE_purposeStmt = 24
    RULE_repeatableStmt = 25
    RULE_actorsStmt = 26
    RULE_focusStmt = 27
    RULE_entryStmt = 28
    RULE_doStmt = 29
    RULE_invariantStmt = 30
    RULE_exitStmt = 31
    RULE_terminalStmt = 32
    RULE_terminalKind = 33
    RULE_joinDecl = 34
    RULE_joinPolicy = 35
    RULE_placeDecl = 36
    RULE_placeTokensStmt = 37
    RULE_capacityStmt = 38
    RULE_transitionDecl = 39
    RULE_arcList = 40
    RULE_arc = 41
    RULE_onStmt = 42
    RULE_whenStmt = 43
    RULE_actionBlock = 44
    RULE_actionStmt = 45
    RULE_nameList = 46
    RULE_bindingSection = 47
    RULE_bindingStmt = 48
    RULE_bindingExpr = 49
    RULE_bindingArgList = 50
    RULE_bindingArg = 51
    RULE_bindingCtor = 52
    RULE_expr = 53
    RULE_implication = 54
    RULE_orExpr = 55
    RULE_andExpr = 56
    RULE_comparison = 57
    RULE_sumExpr = 58
    RULE_productExpr = 59
    RULE_unaryExpr = 60
    RULE_atom = 61
    RULE_callExpr = 62
    RULE_argumentList = 63
    RULE_literal = 64

    ruleNames =  [ "document", "strategyDecl", "worldSection", "entityDecl", 
                   "entityBody", "propertyStmt", "propertyValue", "softId", 
                   "listValue", "initialSection", "exprStmt", "intentSection", 
                   "patternStmt", "patternRoleBinding", "primaryStmt", "secondaryStmt", 
                   "successStmt", "failureStmt", "semanticsSection", "derivedDecl", 
                   "planSection", "startStmt", "planNode", "phaseDecl", 
                   "purposeStmt", "repeatableStmt", "actorsStmt", "focusStmt", 
                   "entryStmt", "doStmt", "invariantStmt", "exitStmt", "terminalStmt", 
                   "terminalKind", "joinDecl", "joinPolicy", "placeDecl", 
                   "placeTokensStmt", "capacityStmt", "transitionDecl", 
                   "arcList", "arc", "onStmt", "whenStmt", "actionBlock", 
                   "actionStmt", "nameList", "bindingSection", "bindingStmt", 
                   "bindingExpr", "bindingArgList", "bindingArg", "bindingCtor", 
                   "expr", "implication", "orExpr", "andExpr", "comparison", 
                   "sumExpr", "productExpr", "unaryExpr", "atom", "callExpr", 
                   "argumentList", "literal" ]

    EOF = Token.EOF
    STRATEGY=1
    WORLD=2
    INITIAL=3
    INTENT=4
    SEMANTICS=5
    DERIVE=6
    PATTERN=7
    PRIMARY=8
    SECONDARY=9
    SUCCESS=10
    FAILURE=11
    FORCE=12
    ASSET=13
    REGION=14
    ROUTE=15
    PLAN=16
    START=17
    PHASE=18
    JOIN=19
    PURPOSE=20
    ACTORS=21
    FOCUS=22
    ENTRY=23
    DO=24
    INVARIANT=25
    EXIT=26
    TERMINAL=27
    TRANSITION=28
    ON=29
    WHEN=30
    PRIORITY=31
    ALL=32
    ANY=33
    ATLEAST=34
    SEQUENCE=35
    PARALLEL=36
    BINDING=37
    PLACE=38
    CAPACITY=39
    REPEATABLE=40
    TRUE=41
    FALSE=42
    NOT=43
    AND=44
    OR=45
    IMPLIES=46
    ARROW=47
    QMARK=48
    COLON=49
    SEMI=50
    COMMA=51
    ASSIGN=52
    EQ=53
    NEQ=54
    BANG=55
    LE=56
    GE=57
    LT=58
    GT=59
    PLUS=60
    MINUS=61
    MUL=62
    DIV=63
    LBRACE=64
    RBRACE=65
    LBRACK=66
    RBRACK=67
    LPAREN=68
    RPAREN=69
    INT=70
    NUMBER=71
    STRING=72
    ID=73
    COMMENT=74
    BLOCK_COMMENT=75
    WS=76

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class DocumentContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def strategyDecl(self):
            return self.getTypedRuleContext(StratagemDSLParser.StrategyDeclContext,0)


        def EOF(self):
            return self.getToken(StratagemDSLParser.EOF, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_document

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDocument" ):
                return visitor.visitDocument(self)
            else:
                return visitor.visitChildren(self)




    def document(self):

        localctx = StratagemDSLParser.DocumentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_document)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 130
            self.strategyDecl()
            self.state = 131
            self.match(StratagemDSLParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StrategyDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRATEGY(self):
            return self.getToken(StratagemDSLParser.STRATEGY, 0)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def worldSection(self):
            return self.getTypedRuleContext(StratagemDSLParser.WorldSectionContext,0)


        def intentSection(self):
            return self.getTypedRuleContext(StratagemDSLParser.IntentSectionContext,0)


        def planSection(self):
            return self.getTypedRuleContext(StratagemDSLParser.PlanSectionContext,0)


        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def initialSection(self):
            return self.getTypedRuleContext(StratagemDSLParser.InitialSectionContext,0)


        def semanticsSection(self):
            return self.getTypedRuleContext(StratagemDSLParser.SemanticsSectionContext,0)


        def bindingSection(self):
            return self.getTypedRuleContext(StratagemDSLParser.BindingSectionContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_strategyDecl

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStrategyDecl" ):
                return visitor.visitStrategyDecl(self)
            else:
                return visitor.visitChildren(self)




    def strategyDecl(self):

        localctx = StratagemDSLParser.StrategyDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_strategyDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 133
            self.match(StratagemDSLParser.STRATEGY)
            self.state = 134
            self.match(StratagemDSLParser.ID)
            self.state = 135
            self.match(StratagemDSLParser.LBRACE)
            self.state = 136
            self.worldSection()
            self.state = 138
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==3:
                self.state = 137
                self.initialSection()


            self.state = 140
            self.intentSection()
            self.state = 142
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 141
                self.semanticsSection()


            self.state = 144
            self.planSection()
            self.state = 146
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==37:
                self.state = 145
                self.bindingSection()


            self.state = 148
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WorldSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WORLD(self):
            return self.getToken(StratagemDSLParser.WORLD, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def entityDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.EntityDeclContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.EntityDeclContext,i)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_worldSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWorldSection" ):
                return visitor.visitWorldSection(self)
            else:
                return visitor.visitChildren(self)




    def worldSection(self):

        localctx = StratagemDSLParser.WorldSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_worldSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 150
            self.match(StratagemDSLParser.WORLD)
            self.state = 151
            self.match(StratagemDSLParser.LBRACE)
            self.state = 155
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 61440) != 0):
                self.state = 152
                self.entityDecl()
                self.state = 157
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 158
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EntityDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_entityDecl

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class AssetDeclContext(EntityDeclContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.EntityDeclContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ASSET(self):
            return self.getToken(StratagemDSLParser.ASSET, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def entityBody(self):
            return self.getTypedRuleContext(StratagemDSLParser.EntityBodyContext,0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssetDecl" ):
                return visitor.visitAssetDecl(self)
            else:
                return visitor.visitChildren(self)


    class ForceDeclContext(EntityDeclContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.EntityDeclContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FORCE(self):
            return self.getToken(StratagemDSLParser.FORCE, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def entityBody(self):
            return self.getTypedRuleContext(StratagemDSLParser.EntityBodyContext,0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForceDecl" ):
                return visitor.visitForceDecl(self)
            else:
                return visitor.visitChildren(self)


    class RegionDeclContext(EntityDeclContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.EntityDeclContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def REGION(self):
            return self.getToken(StratagemDSLParser.REGION, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def entityBody(self):
            return self.getTypedRuleContext(StratagemDSLParser.EntityBodyContext,0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRegionDecl" ):
                return visitor.visitRegionDecl(self)
            else:
                return visitor.visitChildren(self)


    class RouteDeclContext(EntityDeclContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.EntityDeclContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ROUTE(self):
            return self.getToken(StratagemDSLParser.ROUTE, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def entityBody(self):
            return self.getTypedRuleContext(StratagemDSLParser.EntityBodyContext,0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRouteDecl" ):
                return visitor.visitRouteDecl(self)
            else:
                return visitor.visitChildren(self)



    def entityDecl(self):

        localctx = StratagemDSLParser.EntityDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_entityDecl)
        self._la = 0 # Token type
        try:
            self.state = 192
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [12]:
                localctx = StratagemDSLParser.ForceDeclContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 160
                self.match(StratagemDSLParser.FORCE)
                self.state = 161
                self.match(StratagemDSLParser.ID)
                self.state = 163
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==64:
                    self.state = 162
                    self.entityBody()


                self.state = 166
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==50:
                    self.state = 165
                    self.match(StratagemDSLParser.SEMI)


                pass
            elif token in [13]:
                localctx = StratagemDSLParser.AssetDeclContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 168
                self.match(StratagemDSLParser.ASSET)
                self.state = 169
                self.match(StratagemDSLParser.ID)
                self.state = 171
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==64:
                    self.state = 170
                    self.entityBody()


                self.state = 174
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==50:
                    self.state = 173
                    self.match(StratagemDSLParser.SEMI)


                pass
            elif token in [14]:
                localctx = StratagemDSLParser.RegionDeclContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 176
                self.match(StratagemDSLParser.REGION)
                self.state = 177
                self.match(StratagemDSLParser.ID)
                self.state = 179
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==64:
                    self.state = 178
                    self.entityBody()


                self.state = 182
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==50:
                    self.state = 181
                    self.match(StratagemDSLParser.SEMI)


                pass
            elif token in [15]:
                localctx = StratagemDSLParser.RouteDeclContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 184
                self.match(StratagemDSLParser.ROUTE)
                self.state = 185
                self.match(StratagemDSLParser.ID)
                self.state = 187
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==64:
                    self.state = 186
                    self.entityBody()


                self.state = 190
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==50:
                    self.state = 189
                    self.match(StratagemDSLParser.SEMI)


                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EntityBodyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def propertyStmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.PropertyStmtContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.PropertyStmtContext,i)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_entityBody

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitEntityBody" ):
                return visitor.visitEntityBody(self)
            else:
                return visitor.visitChildren(self)




    def entityBody(self):

        localctx = StratagemDSLParser.EntityBodyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_entityBody)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 194
            self.match(StratagemDSLParser.LBRACE)
            self.state = 198
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 2199023255550) != 0) or _la==73:
                self.state = 195
                self.propertyStmt()
                self.state = 200
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 201
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertyStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def softId(self):
            return self.getTypedRuleContext(StratagemDSLParser.SoftIdContext,0)


        def ASSIGN(self):
            return self.getToken(StratagemDSLParser.ASSIGN, 0)

        def propertyValue(self):
            return self.getTypedRuleContext(StratagemDSLParser.PropertyValueContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_propertyStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyStmt" ):
                return visitor.visitPropertyStmt(self)
            else:
                return visitor.visitChildren(self)




    def propertyStmt(self):

        localctx = StratagemDSLParser.PropertyStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_propertyStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 203
            self.softId()
            self.state = 204
            self.match(StratagemDSLParser.ASSIGN)
            self.state = 205
            self.propertyValue()
            self.state = 206
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertyValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_propertyValue

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class NameLitContext(PropertyValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PropertyValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def softId(self):
            return self.getTypedRuleContext(StratagemDSLParser.SoftIdContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNameLit" ):
                return visitor.visitNameLit(self)
            else:
                return visitor.visitChildren(self)


    class FalseLitContext(PropertyValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PropertyValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FALSE(self):
            return self.getToken(StratagemDSLParser.FALSE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFalseLit" ):
                return visitor.visitFalseLit(self)
            else:
                return visitor.visitChildren(self)


    class ListLitContext(PropertyValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PropertyValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def listValue(self):
            return self.getTypedRuleContext(StratagemDSLParser.ListValueContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitListLit" ):
                return visitor.visitListLit(self)
            else:
                return visitor.visitChildren(self)


    class TrueLitContext(PropertyValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PropertyValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def TRUE(self):
            return self.getToken(StratagemDSLParser.TRUE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTrueLit" ):
                return visitor.visitTrueLit(self)
            else:
                return visitor.visitChildren(self)


    class NumLitContext(PropertyValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PropertyValueContext
            super().__init__(parser)
            self._MINUS = None # Token
            self._INT = None # Token
            self._NUMBER = None # Token
            self.copyFrom(ctx)

        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)
        def NUMBER(self):
            return self.getToken(StratagemDSLParser.NUMBER, 0)
        def MINUS(self):
            return self.getToken(StratagemDSLParser.MINUS, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumLit" ):
                return visitor.visitNumLit(self)
            else:
                return visitor.visitChildren(self)


    class StrLitContext(PropertyValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PropertyValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def STRING(self):
            return self.getToken(StratagemDSLParser.STRING, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStrLit" ):
                return visitor.visitStrLit(self)
            else:
                return visitor.visitChildren(self)



    def propertyValue(self):

        localctx = StratagemDSLParser.PropertyValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_propertyValue)
        try:
            self.state = 221
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,14,self._ctx)
            if la_ == 1:
                localctx = StratagemDSLParser.StrLitContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 208
                self.match(StratagemDSLParser.STRING)
                pass

            elif la_ == 2:
                localctx = StratagemDSLParser.NumLitContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 209
                self.match(StratagemDSLParser.INT)
                pass

            elif la_ == 3:
                localctx = StratagemDSLParser.NumLitContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 210
                self.match(StratagemDSLParser.NUMBER)
                pass

            elif la_ == 4:
                localctx = StratagemDSLParser.NumLitContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 211
                localctx._MINUS = self.match(StratagemDSLParser.MINUS)
                self.state = 212
                localctx._INT = self.match(StratagemDSLParser.INT)
                self.state = 213
                if not (0 if localctx._INT is None else localctx._INT.line) * 100000 + (0 if localctx._INT is None else localctx._INT.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1:
                    from antlr4.error.Errors import FailedPredicateException
                    raise FailedPredicateException(self, "$INT.line * 100000 + $INT.pos == $MINUS.line * 100000 + $MINUS.pos + 1")
                pass

            elif la_ == 5:
                localctx = StratagemDSLParser.NumLitContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 214
                localctx._MINUS = self.match(StratagemDSLParser.MINUS)
                self.state = 215
                localctx._NUMBER = self.match(StratagemDSLParser.NUMBER)
                self.state = 216
                if not (0 if localctx._NUMBER is None else localctx._NUMBER.line) * 100000 + (0 if localctx._NUMBER is None else localctx._NUMBER.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1:
                    from antlr4.error.Errors import FailedPredicateException
                    raise FailedPredicateException(self, "$NUMBER.line * 100000 + $NUMBER.pos == $MINUS.line * 100000 + $MINUS.pos + 1")
                pass

            elif la_ == 6:
                localctx = StratagemDSLParser.TrueLitContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 217
                self.match(StratagemDSLParser.TRUE)
                pass

            elif la_ == 7:
                localctx = StratagemDSLParser.FalseLitContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 218
                self.match(StratagemDSLParser.FALSE)
                pass

            elif la_ == 8:
                localctx = StratagemDSLParser.NameLitContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 219
                self.softId()
                pass

            elif la_ == 9:
                localctx = StratagemDSLParser.ListLitContext(self, localctx)
                self.enterOuterAlt(localctx, 9)
                self.state = 220
                self.listValue()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SoftIdContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def STRATEGY(self):
            return self.getToken(StratagemDSLParser.STRATEGY, 0)

        def WORLD(self):
            return self.getToken(StratagemDSLParser.WORLD, 0)

        def INITIAL(self):
            return self.getToken(StratagemDSLParser.INITIAL, 0)

        def INTENT(self):
            return self.getToken(StratagemDSLParser.INTENT, 0)

        def SEMANTICS(self):
            return self.getToken(StratagemDSLParser.SEMANTICS, 0)

        def DERIVE(self):
            return self.getToken(StratagemDSLParser.DERIVE, 0)

        def PATTERN(self):
            return self.getToken(StratagemDSLParser.PATTERN, 0)

        def PRIMARY(self):
            return self.getToken(StratagemDSLParser.PRIMARY, 0)

        def SECONDARY(self):
            return self.getToken(StratagemDSLParser.SECONDARY, 0)

        def SUCCESS(self):
            return self.getToken(StratagemDSLParser.SUCCESS, 0)

        def FAILURE(self):
            return self.getToken(StratagemDSLParser.FAILURE, 0)

        def FORCE(self):
            return self.getToken(StratagemDSLParser.FORCE, 0)

        def ASSET(self):
            return self.getToken(StratagemDSLParser.ASSET, 0)

        def REGION(self):
            return self.getToken(StratagemDSLParser.REGION, 0)

        def ROUTE(self):
            return self.getToken(StratagemDSLParser.ROUTE, 0)

        def PLAN(self):
            return self.getToken(StratagemDSLParser.PLAN, 0)

        def START(self):
            return self.getToken(StratagemDSLParser.START, 0)

        def PHASE(self):
            return self.getToken(StratagemDSLParser.PHASE, 0)

        def JOIN(self):
            return self.getToken(StratagemDSLParser.JOIN, 0)

        def PURPOSE(self):
            return self.getToken(StratagemDSLParser.PURPOSE, 0)

        def ACTORS(self):
            return self.getToken(StratagemDSLParser.ACTORS, 0)

        def FOCUS(self):
            return self.getToken(StratagemDSLParser.FOCUS, 0)

        def ENTRY(self):
            return self.getToken(StratagemDSLParser.ENTRY, 0)

        def DO(self):
            return self.getToken(StratagemDSLParser.DO, 0)

        def INVARIANT(self):
            return self.getToken(StratagemDSLParser.INVARIANT, 0)

        def EXIT(self):
            return self.getToken(StratagemDSLParser.EXIT, 0)

        def TERMINAL(self):
            return self.getToken(StratagemDSLParser.TERMINAL, 0)

        def TRANSITION(self):
            return self.getToken(StratagemDSLParser.TRANSITION, 0)

        def ON(self):
            return self.getToken(StratagemDSLParser.ON, 0)

        def WHEN(self):
            return self.getToken(StratagemDSLParser.WHEN, 0)

        def PRIORITY(self):
            return self.getToken(StratagemDSLParser.PRIORITY, 0)

        def ALL(self):
            return self.getToken(StratagemDSLParser.ALL, 0)

        def ANY(self):
            return self.getToken(StratagemDSLParser.ANY, 0)

        def ATLEAST(self):
            return self.getToken(StratagemDSLParser.ATLEAST, 0)

        def SEQUENCE(self):
            return self.getToken(StratagemDSLParser.SEQUENCE, 0)

        def PARALLEL(self):
            return self.getToken(StratagemDSLParser.PARALLEL, 0)

        def BINDING(self):
            return self.getToken(StratagemDSLParser.BINDING, 0)

        def PLACE(self):
            return self.getToken(StratagemDSLParser.PLACE, 0)

        def CAPACITY(self):
            return self.getToken(StratagemDSLParser.CAPACITY, 0)

        def REPEATABLE(self):
            return self.getToken(StratagemDSLParser.REPEATABLE, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_softId

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSoftId" ):
                return visitor.visitSoftId(self)
            else:
                return visitor.visitChildren(self)




    def softId(self):

        localctx = StratagemDSLParser.SoftIdContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_softId)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 223
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 2199023255550) != 0) or _la==73):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ListValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LBRACK(self):
            return self.getToken(StratagemDSLParser.LBRACK, 0)

        def RBRACK(self):
            return self.getToken(StratagemDSLParser.RBRACK, 0)

        def propertyValue(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.PropertyValueContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.PropertyValueContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.COMMA)
            else:
                return self.getToken(StratagemDSLParser.COMMA, i)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_listValue

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitListValue" ):
                return visitor.visitListValue(self)
            else:
                return visitor.visitChildren(self)




    def listValue(self):

        localctx = StratagemDSLParser.ListValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_listValue)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 225
            self.match(StratagemDSLParser.LBRACK)
            self.state = 234
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 2305851805306716158) != 0) or ((((_la - 66)) & ~0x3f) == 0 and ((1 << (_la - 66)) & 241) != 0):
                self.state = 226
                self.propertyValue()
                self.state = 231
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==51:
                    self.state = 227
                    self.match(StratagemDSLParser.COMMA)
                    self.state = 228
                    self.propertyValue()
                    self.state = 233
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)



            self.state = 236
            self.match(StratagemDSLParser.RBRACK)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class InitialSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INITIAL(self):
            return self.getToken(StratagemDSLParser.INITIAL, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def exprStmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.ExprStmtContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.ExprStmtContext,i)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_initialSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInitialSection" ):
                return visitor.visitInitialSection(self)
            else:
                return visitor.visitChildren(self)




    def initialSection(self):

        localctx = StratagemDSLParser.InitialSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_initialSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 238
            self.match(StratagemDSLParser.INITIAL)
            self.state = 239
            self.match(StratagemDSLParser.LBRACE)
            self.state = 243
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while ((((_la - 41)) & ~0x3f) == 0 and ((1 << (_la - 41)) & 8188329991) != 0):
                self.state = 240
                self.exprStmt()
                self.state = 245
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 246
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExprStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_exprStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExprStmt" ):
                return visitor.visitExprStmt(self)
            else:
                return visitor.visitChildren(self)




    def exprStmt(self):

        localctx = StratagemDSLParser.ExprStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_exprStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 248
            self.expr()
            self.state = 249
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IntentSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INTENT(self):
            return self.getToken(StratagemDSLParser.INTENT, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def primaryStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.PrimaryStmtContext,0)


        def successStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.SuccessStmtContext,0)


        def failureStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.FailureStmtContext,0)


        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def patternStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.PatternStmtContext,0)


        def secondaryStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.SecondaryStmtContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_intentSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntentSection" ):
                return visitor.visitIntentSection(self)
            else:
                return visitor.visitChildren(self)




    def intentSection(self):

        localctx = StratagemDSLParser.IntentSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_intentSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 251
            self.match(StratagemDSLParser.INTENT)
            self.state = 252
            self.match(StratagemDSLParser.LBRACE)
            self.state = 254
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7:
                self.state = 253
                self.patternStmt()


            self.state = 256
            self.primaryStmt()
            self.state = 258
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==9:
                self.state = 257
                self.secondaryStmt()


            self.state = 260
            self.successStmt()
            self.state = 261
            self.failureStmt()
            self.state = 262
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PatternStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_patternStmt

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class PatternBoundContext(PatternStmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PatternStmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def PATTERN(self):
            return self.getToken(StratagemDSLParser.PATTERN, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)
        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)
        def patternRoleBinding(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.PatternRoleBindingContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.PatternRoleBindingContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPatternBound" ):
                return visitor.visitPatternBound(self)
            else:
                return visitor.visitChildren(self)


    class PatternSimpleContext(PatternStmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.PatternStmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def PATTERN(self):
            return self.getToken(StratagemDSLParser.PATTERN, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPatternSimple" ):
                return visitor.visitPatternSimple(self)
            else:
                return visitor.visitChildren(self)



    def patternStmt(self):

        localctx = StratagemDSLParser.PatternStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_patternStmt)
        self._la = 0 # Token type
        try:
            self.state = 277
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,21,self._ctx)
            if la_ == 1:
                localctx = StratagemDSLParser.PatternSimpleContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 264
                self.match(StratagemDSLParser.PATTERN)
                self.state = 265
                self.match(StratagemDSLParser.ID)
                self.state = 266
                self.match(StratagemDSLParser.SEMI)
                pass

            elif la_ == 2:
                localctx = StratagemDSLParser.PatternBoundContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 267
                self.match(StratagemDSLParser.PATTERN)
                self.state = 268
                self.match(StratagemDSLParser.ID)
                self.state = 269
                self.match(StratagemDSLParser.LBRACE)
                self.state = 273
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==73:
                    self.state = 270
                    self.patternRoleBinding()
                    self.state = 275
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 276
                self.match(StratagemDSLParser.RBRACE)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PatternRoleBindingContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.ID)
            else:
                return self.getToken(StratagemDSLParser.ID, i)

        def ASSIGN(self):
            return self.getToken(StratagemDSLParser.ASSIGN, 0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_patternRoleBinding

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPatternRoleBinding" ):
                return visitor.visitPatternRoleBinding(self)
            else:
                return visitor.visitChildren(self)




    def patternRoleBinding(self):

        localctx = StratagemDSLParser.PatternRoleBindingContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_patternRoleBinding)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 279
            self.match(StratagemDSLParser.ID)
            self.state = 280
            self.match(StratagemDSLParser.ASSIGN)
            self.state = 281
            self.match(StratagemDSLParser.ID)
            self.state = 282
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PrimaryStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PRIMARY(self):
            return self.getToken(StratagemDSLParser.PRIMARY, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_primaryStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPrimaryStmt" ):
                return visitor.visitPrimaryStmt(self)
            else:
                return visitor.visitChildren(self)




    def primaryStmt(self):

        localctx = StratagemDSLParser.PrimaryStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_primaryStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 284
            self.match(StratagemDSLParser.PRIMARY)
            self.state = 285
            self.expr()
            self.state = 286
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SecondaryStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SECONDARY(self):
            return self.getToken(StratagemDSLParser.SECONDARY, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_secondaryStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSecondaryStmt" ):
                return visitor.visitSecondaryStmt(self)
            else:
                return visitor.visitChildren(self)




    def secondaryStmt(self):

        localctx = StratagemDSLParser.SecondaryStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_secondaryStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 288
            self.match(StratagemDSLParser.SECONDARY)
            self.state = 289
            self.expr()
            self.state = 290
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SuccessStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SUCCESS(self):
            return self.getToken(StratagemDSLParser.SUCCESS, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_successStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSuccessStmt" ):
                return visitor.visitSuccessStmt(self)
            else:
                return visitor.visitChildren(self)




    def successStmt(self):

        localctx = StratagemDSLParser.SuccessStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_successStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 292
            self.match(StratagemDSLParser.SUCCESS)
            self.state = 293
            self.expr()
            self.state = 294
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FailureStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FAILURE(self):
            return self.getToken(StratagemDSLParser.FAILURE, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_failureStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFailureStmt" ):
                return visitor.visitFailureStmt(self)
            else:
                return visitor.visitChildren(self)




    def failureStmt(self):

        localctx = StratagemDSLParser.FailureStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_failureStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 296
            self.match(StratagemDSLParser.FAILURE)
            self.state = 297
            self.expr()
            self.state = 298
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SemanticsSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SEMANTICS(self):
            return self.getToken(StratagemDSLParser.SEMANTICS, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def derivedDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.DerivedDeclContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.DerivedDeclContext,i)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_semanticsSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSemanticsSection" ):
                return visitor.visitSemanticsSection(self)
            else:
                return visitor.visitChildren(self)




    def semanticsSection(self):

        localctx = StratagemDSLParser.SemanticsSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_semanticsSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 300
            self.match(StratagemDSLParser.SEMANTICS)
            self.state = 301
            self.match(StratagemDSLParser.LBRACE)
            self.state = 305
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==6:
                self.state = 302
                self.derivedDecl()
                self.state = 307
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 308
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DerivedDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DERIVE(self):
            return self.getToken(StratagemDSLParser.DERIVE, 0)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def ASSIGN(self):
            return self.getToken(StratagemDSLParser.ASSIGN, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_derivedDecl

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDerivedDecl" ):
                return visitor.visitDerivedDecl(self)
            else:
                return visitor.visitChildren(self)




    def derivedDecl(self):

        localctx = StratagemDSLParser.DerivedDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_derivedDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 310
            self.match(StratagemDSLParser.DERIVE)
            self.state = 311
            self.match(StratagemDSLParser.ID)
            self.state = 312
            self.match(StratagemDSLParser.ASSIGN)
            self.state = 313
            self.expr()
            self.state = 314
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PlanSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PLAN(self):
            return self.getToken(StratagemDSLParser.PLAN, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def startStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.StartStmtContext,0)


        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def planNode(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.PlanNodeContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.PlanNodeContext,i)


        def transitionDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.TransitionDeclContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.TransitionDeclContext,i)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_planSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPlanSection" ):
                return visitor.visitPlanSection(self)
            else:
                return visitor.visitChildren(self)




    def planSection(self):

        localctx = StratagemDSLParser.PlanSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_planSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 316
            self.match(StratagemDSLParser.PLAN)
            self.state = 317
            self.match(StratagemDSLParser.LBRACE)
            self.state = 318
            self.startStmt()
            self.state = 320 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 319
                self.planNode()
                self.state = 322 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & 274878693376) != 0)):
                    break

            self.state = 327
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==28:
                self.state = 324
                self.transitionDecl()
                self.state = 329
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 330
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StartStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def START(self):
            return self.getToken(StratagemDSLParser.START, 0)

        def nameList(self):
            return self.getTypedRuleContext(StratagemDSLParser.NameListContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_startStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStartStmt" ):
                return visitor.visitStartStmt(self)
            else:
                return visitor.visitChildren(self)




    def startStmt(self):

        localctx = StratagemDSLParser.StartStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_startStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 332
            self.match(StratagemDSLParser.START)
            self.state = 333
            self.nameList()
            self.state = 334
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PlanNodeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def phaseDecl(self):
            return self.getTypedRuleContext(StratagemDSLParser.PhaseDeclContext,0)


        def joinDecl(self):
            return self.getTypedRuleContext(StratagemDSLParser.JoinDeclContext,0)


        def placeDecl(self):
            return self.getTypedRuleContext(StratagemDSLParser.PlaceDeclContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_planNode

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPlanNode" ):
                return visitor.visitPlanNode(self)
            else:
                return visitor.visitChildren(self)




    def planNode(self):

        localctx = StratagemDSLParser.PlanNodeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_planNode)
        try:
            self.state = 339
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [18]:
                self.enterOuterAlt(localctx, 1)
                self.state = 336
                self.phaseDecl()
                pass
            elif token in [19]:
                self.enterOuterAlt(localctx, 2)
                self.state = 337
                self.joinDecl()
                pass
            elif token in [38]:
                self.enterOuterAlt(localctx, 3)
                self.state = 338
                self.placeDecl()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PhaseDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PHASE(self):
            return self.getToken(StratagemDSLParser.PHASE, 0)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def purposeStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.PurposeStmtContext,0)


        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def repeatableStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.RepeatableStmtContext,0)


        def actorsStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.ActorsStmtContext,0)


        def focusStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.FocusStmtContext,0)


        def entryStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.EntryStmtContext,0)


        def doStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.DoStmtContext,0)


        def invariantStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.InvariantStmtContext,0)


        def exitStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExitStmtContext,0)


        def terminalStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.TerminalStmtContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_phaseDecl

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPhaseDecl" ):
                return visitor.visitPhaseDecl(self)
            else:
                return visitor.visitChildren(self)




    def phaseDecl(self):

        localctx = StratagemDSLParser.PhaseDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_phaseDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 341
            self.match(StratagemDSLParser.PHASE)
            self.state = 342
            self.match(StratagemDSLParser.ID)
            self.state = 343
            self.match(StratagemDSLParser.LBRACE)
            self.state = 344
            self.purposeStmt()
            self.state = 346
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==40:
                self.state = 345
                self.repeatableStmt()


            self.state = 349
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 348
                self.actorsStmt()


            self.state = 352
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==22:
                self.state = 351
                self.focusStmt()


            self.state = 355
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==23:
                self.state = 354
                self.entryStmt()


            self.state = 358
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==24:
                self.state = 357
                self.doStmt()


            self.state = 361
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==25:
                self.state = 360
                self.invariantStmt()


            self.state = 364
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==26:
                self.state = 363
                self.exitStmt()


            self.state = 367
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==27:
                self.state = 366
                self.terminalStmt()


            self.state = 369
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PurposeStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PURPOSE(self):
            return self.getToken(StratagemDSLParser.PURPOSE, 0)

        def STRING(self):
            return self.getToken(StratagemDSLParser.STRING, 0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_purposeStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPurposeStmt" ):
                return visitor.visitPurposeStmt(self)
            else:
                return visitor.visitChildren(self)




    def purposeStmt(self):

        localctx = StratagemDSLParser.PurposeStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_purposeStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 371
            self.match(StratagemDSLParser.PURPOSE)
            self.state = 372
            self.match(StratagemDSLParser.STRING)
            self.state = 373
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RepeatableStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def REPEATABLE(self):
            return self.getToken(StratagemDSLParser.REPEATABLE, 0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_repeatableStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRepeatableStmt" ):
                return visitor.visitRepeatableStmt(self)
            else:
                return visitor.visitChildren(self)




    def repeatableStmt(self):

        localctx = StratagemDSLParser.RepeatableStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_repeatableStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 375
            self.match(StratagemDSLParser.REPEATABLE)
            self.state = 376
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ActorsStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ACTORS(self):
            return self.getToken(StratagemDSLParser.ACTORS, 0)

        def nameList(self):
            return self.getTypedRuleContext(StratagemDSLParser.NameListContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_actorsStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitActorsStmt" ):
                return visitor.visitActorsStmt(self)
            else:
                return visitor.visitChildren(self)




    def actorsStmt(self):

        localctx = StratagemDSLParser.ActorsStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 52, self.RULE_actorsStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 378
            self.match(StratagemDSLParser.ACTORS)
            self.state = 379
            self.nameList()
            self.state = 380
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FocusStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FOCUS(self):
            return self.getToken(StratagemDSLParser.FOCUS, 0)

        def nameList(self):
            return self.getTypedRuleContext(StratagemDSLParser.NameListContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_focusStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFocusStmt" ):
                return visitor.visitFocusStmt(self)
            else:
                return visitor.visitChildren(self)




    def focusStmt(self):

        localctx = StratagemDSLParser.FocusStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_focusStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 382
            self.match(StratagemDSLParser.FOCUS)
            self.state = 383
            self.nameList()
            self.state = 384
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EntryStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ENTRY(self):
            return self.getToken(StratagemDSLParser.ENTRY, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_entryStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitEntryStmt" ):
                return visitor.visitEntryStmt(self)
            else:
                return visitor.visitChildren(self)




    def entryStmt(self):

        localctx = StratagemDSLParser.EntryStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 56, self.RULE_entryStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 386
            self.match(StratagemDSLParser.ENTRY)
            self.state = 387
            self.expr()
            self.state = 388
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DoStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DO(self):
            return self.getToken(StratagemDSLParser.DO, 0)

        def actionBlock(self):
            return self.getTypedRuleContext(StratagemDSLParser.ActionBlockContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_doStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDoStmt" ):
                return visitor.visitDoStmt(self)
            else:
                return visitor.visitChildren(self)




    def doStmt(self):

        localctx = StratagemDSLParser.DoStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 58, self.RULE_doStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 390
            self.match(StratagemDSLParser.DO)
            self.state = 391
            self.actionBlock()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class InvariantStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INVARIANT(self):
            return self.getToken(StratagemDSLParser.INVARIANT, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_invariantStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInvariantStmt" ):
                return visitor.visitInvariantStmt(self)
            else:
                return visitor.visitChildren(self)




    def invariantStmt(self):

        localctx = StratagemDSLParser.InvariantStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 60, self.RULE_invariantStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 393
            self.match(StratagemDSLParser.INVARIANT)
            self.state = 394
            self.expr()
            self.state = 395
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExitStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EXIT(self):
            return self.getToken(StratagemDSLParser.EXIT, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_exitStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExitStmt" ):
                return visitor.visitExitStmt(self)
            else:
                return visitor.visitChildren(self)




    def exitStmt(self):

        localctx = StratagemDSLParser.ExitStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 62, self.RULE_exitStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 397
            self.match(StratagemDSLParser.EXIT)
            self.state = 398
            self.expr()
            self.state = 399
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TerminalStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TERMINAL(self):
            return self.getToken(StratagemDSLParser.TERMINAL, 0)

        def terminalKind(self):
            return self.getTypedRuleContext(StratagemDSLParser.TerminalKindContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_terminalStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTerminalStmt" ):
                return visitor.visitTerminalStmt(self)
            else:
                return visitor.visitChildren(self)




    def terminalStmt(self):

        localctx = StratagemDSLParser.TerminalStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_terminalStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 401
            self.match(StratagemDSLParser.TERMINAL)
            self.state = 402
            self.terminalKind()
            self.state = 403
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TerminalKindContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_terminalKind

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class TerminalSuccessContext(TerminalKindContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.TerminalKindContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SUCCESS(self):
            return self.getToken(StratagemDSLParser.SUCCESS, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTerminalSuccess" ):
                return visitor.visitTerminalSuccess(self)
            else:
                return visitor.visitChildren(self)


    class TerminalFailureContext(TerminalKindContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.TerminalKindContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FAILURE(self):
            return self.getToken(StratagemDSLParser.FAILURE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTerminalFailure" ):
                return visitor.visitTerminalFailure(self)
            else:
                return visitor.visitChildren(self)



    def terminalKind(self):

        localctx = StratagemDSLParser.TerminalKindContext(self, self._ctx, self.state)
        self.enterRule(localctx, 66, self.RULE_terminalKind)
        try:
            self.state = 407
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [10]:
                localctx = StratagemDSLParser.TerminalSuccessContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 405
                self.match(StratagemDSLParser.SUCCESS)
                pass
            elif token in [11]:
                localctx = StratagemDSLParser.TerminalFailureContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 406
                self.match(StratagemDSLParser.FAILURE)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class JoinDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def JOIN(self):
            return self.getToken(StratagemDSLParser.JOIN, 0)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def joinPolicy(self):
            return self.getTypedRuleContext(StratagemDSLParser.JoinPolicyContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_joinDecl

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitJoinDecl" ):
                return visitor.visitJoinDecl(self)
            else:
                return visitor.visitChildren(self)




    def joinDecl(self):

        localctx = StratagemDSLParser.JoinDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 68, self.RULE_joinDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 409
            self.match(StratagemDSLParser.JOIN)
            self.state = 410
            self.match(StratagemDSLParser.ID)
            self.state = 411
            self.joinPolicy()
            self.state = 412
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class JoinPolicyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_joinPolicy

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class JoinAnyContext(JoinPolicyContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.JoinPolicyContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ANY(self):
            return self.getToken(StratagemDSLParser.ANY, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitJoinAny" ):
                return visitor.visitJoinAny(self)
            else:
                return visitor.visitChildren(self)


    class JoinAtleastContext(JoinPolicyContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.JoinPolicyContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ATLEAST(self):
            return self.getToken(StratagemDSLParser.ATLEAST, 0)
        def LPAREN(self):
            return self.getToken(StratagemDSLParser.LPAREN, 0)
        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)
        def RPAREN(self):
            return self.getToken(StratagemDSLParser.RPAREN, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitJoinAtleast" ):
                return visitor.visitJoinAtleast(self)
            else:
                return visitor.visitChildren(self)


    class JoinAllContext(JoinPolicyContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.JoinPolicyContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ALL(self):
            return self.getToken(StratagemDSLParser.ALL, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitJoinAll" ):
                return visitor.visitJoinAll(self)
            else:
                return visitor.visitChildren(self)



    def joinPolicy(self):

        localctx = StratagemDSLParser.JoinPolicyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 70, self.RULE_joinPolicy)
        try:
            self.state = 420
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [32]:
                localctx = StratagemDSLParser.JoinAllContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 414
                self.match(StratagemDSLParser.ALL)
                pass
            elif token in [33]:
                localctx = StratagemDSLParser.JoinAnyContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 415
                self.match(StratagemDSLParser.ANY)
                pass
            elif token in [34]:
                localctx = StratagemDSLParser.JoinAtleastContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 416
                self.match(StratagemDSLParser.ATLEAST)
                self.state = 417
                self.match(StratagemDSLParser.LPAREN)
                self.state = 418
                self.match(StratagemDSLParser.INT)
                self.state = 419
                self.match(StratagemDSLParser.RPAREN)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PlaceDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PLACE(self):
            return self.getToken(StratagemDSLParser.PLACE, 0)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def purposeStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.PurposeStmtContext,0)


        def placeTokensStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.PlaceTokensStmtContext,0)


        def capacityStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.CapacityStmtContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_placeDecl

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPlaceDecl" ):
                return visitor.visitPlaceDecl(self)
            else:
                return visitor.visitChildren(self)




    def placeDecl(self):

        localctx = StratagemDSLParser.PlaceDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 72, self.RULE_placeDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 422
            self.match(StratagemDSLParser.PLACE)
            self.state = 423
            self.match(StratagemDSLParser.ID)
            self.state = 424
            self.match(StratagemDSLParser.LBRACE)
            self.state = 426
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==20:
                self.state = 425
                self.purposeStmt()


            self.state = 429
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==3:
                self.state = 428
                self.placeTokensStmt()


            self.state = 432
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==39:
                self.state = 431
                self.capacityStmt()


            self.state = 434
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PlaceTokensStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INITIAL(self):
            return self.getToken(StratagemDSLParser.INITIAL, 0)

        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_placeTokensStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPlaceTokensStmt" ):
                return visitor.visitPlaceTokensStmt(self)
            else:
                return visitor.visitChildren(self)




    def placeTokensStmt(self):

        localctx = StratagemDSLParser.PlaceTokensStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 74, self.RULE_placeTokensStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 436
            self.match(StratagemDSLParser.INITIAL)
            self.state = 437
            self.match(StratagemDSLParser.INT)
            self.state = 438
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CapacityStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CAPACITY(self):
            return self.getToken(StratagemDSLParser.CAPACITY, 0)

        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_capacityStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCapacityStmt" ):
                return visitor.visitCapacityStmt(self)
            else:
                return visitor.visitChildren(self)




    def capacityStmt(self):

        localctx = StratagemDSLParser.CapacityStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 76, self.RULE_capacityStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 440
            self.match(StratagemDSLParser.CAPACITY)
            self.state = 441
            self.match(StratagemDSLParser.INT)
            self.state = 442
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TransitionDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TRANSITION(self):
            return self.getToken(StratagemDSLParser.TRANSITION, 0)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def COLON(self):
            return self.getToken(StratagemDSLParser.COLON, 0)

        def arcList(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.ArcListContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.ArcListContext,i)


        def ARROW(self):
            return self.getToken(StratagemDSLParser.ARROW, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def PRIORITY(self):
            return self.getToken(StratagemDSLParser.PRIORITY, 0)

        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)

        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def onStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.OnStmtContext,0)


        def whenStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.WhenStmtContext,0)


        def doStmt(self):
            return self.getTypedRuleContext(StratagemDSLParser.DoStmtContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_transitionDecl

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTransitionDecl" ):
                return visitor.visitTransitionDecl(self)
            else:
                return visitor.visitChildren(self)




    def transitionDecl(self):

        localctx = StratagemDSLParser.TransitionDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 78, self.RULE_transitionDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 444
            self.match(StratagemDSLParser.TRANSITION)
            self.state = 445
            self.match(StratagemDSLParser.ID)
            self.state = 446
            self.match(StratagemDSLParser.COLON)
            self.state = 447
            self.arcList()
            self.state = 448
            self.match(StratagemDSLParser.ARROW)
            self.state = 449
            self.arcList()
            self.state = 450
            self.match(StratagemDSLParser.LBRACE)
            self.state = 452
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==29:
                self.state = 451
                self.onStmt()


            self.state = 455
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==30:
                self.state = 454
                self.whenStmt()


            self.state = 458
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==24:
                self.state = 457
                self.doStmt()


            self.state = 460
            self.match(StratagemDSLParser.PRIORITY)
            self.state = 461
            self.match(StratagemDSLParser.INT)
            self.state = 462
            self.match(StratagemDSLParser.SEMI)
            self.state = 463
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArcListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def arc(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.ArcContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.ArcContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.COMMA)
            else:
                return self.getToken(StratagemDSLParser.COMMA, i)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_arcList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArcList" ):
                return visitor.visitArcList(self)
            else:
                return visitor.visitChildren(self)




    def arcList(self):

        localctx = StratagemDSLParser.ArcListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 80, self.RULE_arcList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 465
            self.arc()
            self.state = 470
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==51:
                self.state = 466
                self.match(StratagemDSLParser.COMMA)
                self.state = 467
                self.arc()
                self.state = 472
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArcContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_arc

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class ArcNormalContext(ArcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ArcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArcNormal" ):
                return visitor.visitArcNormal(self)
            else:
                return visitor.visitChildren(self)


    class ArcReadWeightedContext(ArcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ArcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def QMARK(self):
            return self.getToken(StratagemDSLParser.QMARK, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def MUL(self):
            return self.getToken(StratagemDSLParser.MUL, 0)
        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArcReadWeighted" ):
                return visitor.visitArcReadWeighted(self)
            else:
                return visitor.visitChildren(self)


    class ArcWeightedContext(ArcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ArcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def MUL(self):
            return self.getToken(StratagemDSLParser.MUL, 0)
        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArcWeighted" ):
                return visitor.visitArcWeighted(self)
            else:
                return visitor.visitChildren(self)


    class ArcInhibitWeightedContext(ArcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ArcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def BANG(self):
            return self.getToken(StratagemDSLParser.BANG, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)
        def MUL(self):
            return self.getToken(StratagemDSLParser.MUL, 0)
        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArcInhibitWeighted" ):
                return visitor.visitArcInhibitWeighted(self)
            else:
                return visitor.visitChildren(self)


    class ArcReadContext(ArcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ArcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def QMARK(self):
            return self.getToken(StratagemDSLParser.QMARK, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArcRead" ):
                return visitor.visitArcRead(self)
            else:
                return visitor.visitChildren(self)


    class ArcInhibitContext(ArcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ArcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def BANG(self):
            return self.getToken(StratagemDSLParser.BANG, 0)
        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArcInhibit" ):
                return visitor.visitArcInhibit(self)
            else:
                return visitor.visitChildren(self)



    def arc(self):

        localctx = StratagemDSLParser.ArcContext(self, self._ctx, self.state)
        self.enterRule(localctx, 82, self.RULE_arc)
        try:
            self.state = 489
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,43,self._ctx)
            if la_ == 1:
                localctx = StratagemDSLParser.ArcNormalContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 473
                self.match(StratagemDSLParser.ID)
                pass

            elif la_ == 2:
                localctx = StratagemDSLParser.ArcWeightedContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 474
                self.match(StratagemDSLParser.ID)
                self.state = 475
                self.match(StratagemDSLParser.MUL)
                self.state = 476
                self.match(StratagemDSLParser.INT)
                pass

            elif la_ == 3:
                localctx = StratagemDSLParser.ArcReadContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 477
                self.match(StratagemDSLParser.QMARK)
                self.state = 478
                self.match(StratagemDSLParser.ID)
                pass

            elif la_ == 4:
                localctx = StratagemDSLParser.ArcReadWeightedContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 479
                self.match(StratagemDSLParser.QMARK)
                self.state = 480
                self.match(StratagemDSLParser.ID)
                self.state = 481
                self.match(StratagemDSLParser.MUL)
                self.state = 482
                self.match(StratagemDSLParser.INT)
                pass

            elif la_ == 5:
                localctx = StratagemDSLParser.ArcInhibitContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 483
                self.match(StratagemDSLParser.BANG)
                self.state = 484
                self.match(StratagemDSLParser.ID)
                pass

            elif la_ == 6:
                localctx = StratagemDSLParser.ArcInhibitWeightedContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 485
                self.match(StratagemDSLParser.BANG)
                self.state = 486
                self.match(StratagemDSLParser.ID)
                self.state = 487
                self.match(StratagemDSLParser.MUL)
                self.state = 488
                self.match(StratagemDSLParser.INT)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OnStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ON(self):
            return self.getToken(StratagemDSLParser.ON, 0)

        def callExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.CallExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_onStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOnStmt" ):
                return visitor.visitOnStmt(self)
            else:
                return visitor.visitChildren(self)




    def onStmt(self):

        localctx = StratagemDSLParser.OnStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 84, self.RULE_onStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 491
            self.match(StratagemDSLParser.ON)
            self.state = 492
            self.callExpr()
            self.state = 493
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WhenStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHEN(self):
            return self.getToken(StratagemDSLParser.WHEN, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_whenStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhenStmt" ):
                return visitor.visitWhenStmt(self)
            else:
                return visitor.visitChildren(self)




    def whenStmt(self):

        localctx = StratagemDSLParser.WhenStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 86, self.RULE_whenStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 495
            self.match(StratagemDSLParser.WHEN)
            self.state = 496
            self.expr()
            self.state = 497
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ActionBlockContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_actionBlock

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class SequentialBlockContext(ActionBlockContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ActionBlockContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)
        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)
        def actionStmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.ActionStmtContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.ActionStmtContext,i)

        def SEQUENCE(self):
            return self.getToken(StratagemDSLParser.SEQUENCE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSequentialBlock" ):
                return visitor.visitSequentialBlock(self)
            else:
                return visitor.visitChildren(self)


    class ParallelBlockContext(ActionBlockContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.ActionBlockContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def PARALLEL(self):
            return self.getToken(StratagemDSLParser.PARALLEL, 0)
        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)
        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)
        def actionStmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.ActionStmtContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.ActionStmtContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParallelBlock" ):
                return visitor.visitParallelBlock(self)
            else:
                return visitor.visitChildren(self)



    def actionBlock(self):

        localctx = StratagemDSLParser.ActionBlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 88, self.RULE_actionBlock)
        self._la = 0 # Token type
        try:
            self.state = 525
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [64]:
                localctx = StratagemDSLParser.SequentialBlockContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 499
                self.match(StratagemDSLParser.LBRACE)
                self.state = 503
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==73:
                    self.state = 500
                    self.actionStmt()
                    self.state = 505
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 506
                self.match(StratagemDSLParser.RBRACE)
                pass
            elif token in [35]:
                localctx = StratagemDSLParser.SequentialBlockContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 507
                self.match(StratagemDSLParser.SEQUENCE)
                self.state = 508
                self.match(StratagemDSLParser.LBRACE)
                self.state = 512
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==73:
                    self.state = 509
                    self.actionStmt()
                    self.state = 514
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 515
                self.match(StratagemDSLParser.RBRACE)
                pass
            elif token in [36]:
                localctx = StratagemDSLParser.ParallelBlockContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 516
                self.match(StratagemDSLParser.PARALLEL)
                self.state = 517
                self.match(StratagemDSLParser.LBRACE)
                self.state = 521
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==73:
                    self.state = 518
                    self.actionStmt()
                    self.state = 523
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 524
                self.match(StratagemDSLParser.RBRACE)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ActionStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def callExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.CallExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_actionStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitActionStmt" ):
                return visitor.visitActionStmt(self)
            else:
                return visitor.visitChildren(self)




    def actionStmt(self):

        localctx = StratagemDSLParser.ActionStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 90, self.RULE_actionStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 527
            self.callExpr()
            self.state = 528
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NameListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LBRACK(self):
            return self.getToken(StratagemDSLParser.LBRACK, 0)

        def RBRACK(self):
            return self.getToken(StratagemDSLParser.RBRACK, 0)

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.ID)
            else:
                return self.getToken(StratagemDSLParser.ID, i)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.COMMA)
            else:
                return self.getToken(StratagemDSLParser.COMMA, i)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_nameList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNameList" ):
                return visitor.visitNameList(self)
            else:
                return visitor.visitChildren(self)




    def nameList(self):

        localctx = StratagemDSLParser.NameListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 92, self.RULE_nameList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 530
            self.match(StratagemDSLParser.LBRACK)
            self.state = 539
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==73:
                self.state = 531
                self.match(StratagemDSLParser.ID)
                self.state = 536
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==51:
                    self.state = 532
                    self.match(StratagemDSLParser.COMMA)
                    self.state = 533
                    self.match(StratagemDSLParser.ID)
                    self.state = 538
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)



            self.state = 541
            self.match(StratagemDSLParser.RBRACK)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BindingSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def BINDING(self):
            return self.getToken(StratagemDSLParser.BINDING, 0)

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def LBRACE(self):
            return self.getToken(StratagemDSLParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(StratagemDSLParser.RBRACE, 0)

        def bindingStmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.BindingStmtContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.BindingStmtContext,i)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_bindingSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingSection" ):
                return visitor.visitBindingSection(self)
            else:
                return visitor.visitChildren(self)




    def bindingSection(self):

        localctx = StratagemDSLParser.BindingSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 94, self.RULE_bindingSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 543
            self.match(StratagemDSLParser.BINDING)
            self.state = 544
            self.match(StratagemDSLParser.ID)
            self.state = 545
            self.match(StratagemDSLParser.LBRACE)
            self.state = 549
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==73:
                self.state = 546
                self.bindingStmt()
                self.state = 551
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 552
            self.match(StratagemDSLParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BindingStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def ASSIGN(self):
            return self.getToken(StratagemDSLParser.ASSIGN, 0)

        def bindingExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.BindingExprContext,0)


        def SEMI(self):
            return self.getToken(StratagemDSLParser.SEMI, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_bindingStmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingStmt" ):
                return visitor.visitBindingStmt(self)
            else:
                return visitor.visitChildren(self)




    def bindingStmt(self):

        localctx = StratagemDSLParser.BindingStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 96, self.RULE_bindingStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 554
            self.match(StratagemDSLParser.ID)
            self.state = 555
            self.match(StratagemDSLParser.ASSIGN)
            self.state = 556
            self.bindingExpr()
            self.state = 557
            self.match(StratagemDSLParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BindingExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_bindingExpr

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class BindingCallContext(BindingExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def bindingCtor(self):
            return self.getTypedRuleContext(StratagemDSLParser.BindingCtorContext,0)

        def LPAREN(self):
            return self.getToken(StratagemDSLParser.LPAREN, 0)
        def RPAREN(self):
            return self.getToken(StratagemDSLParser.RPAREN, 0)
        def bindingArgList(self):
            return self.getTypedRuleContext(StratagemDSLParser.BindingArgListContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingCall" ):
                return visitor.visitBindingCall(self)
            else:
                return visitor.visitChildren(self)


    class BindingNumberContext(BindingExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingExprContext
            super().__init__(parser)
            self._MINUS = None # Token
            self._INT = None # Token
            self._NUMBER = None # Token
            self.copyFrom(ctx)

        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)
        def NUMBER(self):
            return self.getToken(StratagemDSLParser.NUMBER, 0)
        def MINUS(self):
            return self.getToken(StratagemDSLParser.MINUS, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingNumber" ):
                return visitor.visitBindingNumber(self)
            else:
                return visitor.visitChildren(self)


    class BindingFalseContext(BindingExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FALSE(self):
            return self.getToken(StratagemDSLParser.FALSE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingFalse" ):
                return visitor.visitBindingFalse(self)
            else:
                return visitor.visitChildren(self)


    class BindingNameContext(BindingExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def softId(self):
            return self.getTypedRuleContext(StratagemDSLParser.SoftIdContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingName" ):
                return visitor.visitBindingName(self)
            else:
                return visitor.visitChildren(self)


    class BindingListContext(BindingExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def LBRACK(self):
            return self.getToken(StratagemDSLParser.LBRACK, 0)
        def RBRACK(self):
            return self.getToken(StratagemDSLParser.RBRACK, 0)
        def bindingExpr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.BindingExprContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.BindingExprContext,i)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.COMMA)
            else:
                return self.getToken(StratagemDSLParser.COMMA, i)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingList" ):
                return visitor.visitBindingList(self)
            else:
                return visitor.visitChildren(self)


    class BindingTrueContext(BindingExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def TRUE(self):
            return self.getToken(StratagemDSLParser.TRUE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingTrue" ):
                return visitor.visitBindingTrue(self)
            else:
                return visitor.visitChildren(self)


    class BindingStringContext(BindingExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def STRING(self):
            return self.getToken(StratagemDSLParser.STRING, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingString" ):
                return visitor.visitBindingString(self)
            else:
                return visitor.visitChildren(self)



    def bindingExpr(self):

        localctx = StratagemDSLParser.BindingExprContext(self, self._ctx, self.state)
        self.enterRule(localctx, 98, self.RULE_bindingExpr)
        self._la = 0 # Token type
        try:
            self.state = 590
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,54,self._ctx)
            if la_ == 1:
                localctx = StratagemDSLParser.BindingCallContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 559
                self.bindingCtor()
                self.state = 560
                self.match(StratagemDSLParser.LPAREN)
                self.state = 562
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 2305851805306716158) != 0) or ((((_la - 66)) & ~0x3f) == 0 and ((1 << (_la - 66)) & 241) != 0):
                    self.state = 561
                    self.bindingArgList()


                self.state = 564
                self.match(StratagemDSLParser.RPAREN)
                pass

            elif la_ == 2:
                localctx = StratagemDSLParser.BindingStringContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 566
                self.match(StratagemDSLParser.STRING)
                pass

            elif la_ == 3:
                localctx = StratagemDSLParser.BindingNumberContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 567
                self.match(StratagemDSLParser.INT)
                pass

            elif la_ == 4:
                localctx = StratagemDSLParser.BindingNumberContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 568
                self.match(StratagemDSLParser.NUMBER)
                pass

            elif la_ == 5:
                localctx = StratagemDSLParser.BindingNumberContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 569
                localctx._MINUS = self.match(StratagemDSLParser.MINUS)
                self.state = 570
                localctx._INT = self.match(StratagemDSLParser.INT)
                self.state = 571
                if not (0 if localctx._INT is None else localctx._INT.line) * 100000 + (0 if localctx._INT is None else localctx._INT.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1:
                    from antlr4.error.Errors import FailedPredicateException
                    raise FailedPredicateException(self, "$INT.line * 100000 + $INT.pos == $MINUS.line * 100000 + $MINUS.pos + 1")
                pass

            elif la_ == 6:
                localctx = StratagemDSLParser.BindingNumberContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 572
                localctx._MINUS = self.match(StratagemDSLParser.MINUS)
                self.state = 573
                localctx._NUMBER = self.match(StratagemDSLParser.NUMBER)
                self.state = 574
                if not (0 if localctx._NUMBER is None else localctx._NUMBER.line) * 100000 + (0 if localctx._NUMBER is None else localctx._NUMBER.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1:
                    from antlr4.error.Errors import FailedPredicateException
                    raise FailedPredicateException(self, "$NUMBER.line * 100000 + $NUMBER.pos == $MINUS.line * 100000 + $MINUS.pos + 1")
                pass

            elif la_ == 7:
                localctx = StratagemDSLParser.BindingTrueContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 575
                self.match(StratagemDSLParser.TRUE)
                pass

            elif la_ == 8:
                localctx = StratagemDSLParser.BindingFalseContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 576
                self.match(StratagemDSLParser.FALSE)
                pass

            elif la_ == 9:
                localctx = StratagemDSLParser.BindingNameContext(self, localctx)
                self.enterOuterAlt(localctx, 9)
                self.state = 577
                self.softId()
                pass

            elif la_ == 10:
                localctx = StratagemDSLParser.BindingListContext(self, localctx)
                self.enterOuterAlt(localctx, 10)
                self.state = 578
                self.match(StratagemDSLParser.LBRACK)
                self.state = 587
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 2305851805306716158) != 0) or ((((_la - 66)) & ~0x3f) == 0 and ((1 << (_la - 66)) & 241) != 0):
                    self.state = 579
                    self.bindingExpr()
                    self.state = 584
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    while _la==51:
                        self.state = 580
                        self.match(StratagemDSLParser.COMMA)
                        self.state = 581
                        self.bindingExpr()
                        self.state = 586
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)



                self.state = 589
                self.match(StratagemDSLParser.RBRACK)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BindingArgListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def bindingArg(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.BindingArgContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.BindingArgContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.COMMA)
            else:
                return self.getToken(StratagemDSLParser.COMMA, i)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_bindingArgList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingArgList" ):
                return visitor.visitBindingArgList(self)
            else:
                return visitor.visitChildren(self)




    def bindingArgList(self):

        localctx = StratagemDSLParser.BindingArgListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 100, self.RULE_bindingArgList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 592
            self.bindingArg()
            self.state = 597
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==51:
                self.state = 593
                self.match(StratagemDSLParser.COMMA)
                self.state = 594
                self.bindingArg()
                self.state = 599
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BindingArgContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_bindingArg

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class PositionalBindingArgContext(BindingArgContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingArgContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def bindingExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.BindingExprContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPositionalBindingArg" ):
                return visitor.visitPositionalBindingArg(self)
            else:
                return visitor.visitChildren(self)


    class NamedBindingArgContext(BindingArgContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.BindingArgContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def softId(self):
            return self.getTypedRuleContext(StratagemDSLParser.SoftIdContext,0)

        def ASSIGN(self):
            return self.getToken(StratagemDSLParser.ASSIGN, 0)
        def bindingExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.BindingExprContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNamedBindingArg" ):
                return visitor.visitNamedBindingArg(self)
            else:
                return visitor.visitChildren(self)



    def bindingArg(self):

        localctx = StratagemDSLParser.BindingArgContext(self, self._ctx, self.state)
        self.enterRule(localctx, 102, self.RULE_bindingArg)
        try:
            self.state = 605
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,56,self._ctx)
            if la_ == 1:
                localctx = StratagemDSLParser.NamedBindingArgContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 600
                self.softId()
                self.state = 601
                self.match(StratagemDSLParser.ASSIGN)
                self.state = 602
                self.bindingExpr()
                pass

            elif la_ == 2:
                localctx = StratagemDSLParser.PositionalBindingArgContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 604
                self.bindingExpr()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BindingCtorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def ROUTE(self):
            return self.getToken(StratagemDSLParser.ROUTE, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_bindingCtor

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBindingCtor" ):
                return visitor.visitBindingCtor(self)
            else:
                return visitor.visitChildren(self)




    def bindingCtor(self):

        localctx = StratagemDSLParser.BindingCtorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 104, self.RULE_bindingCtor)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 607
            _la = self._input.LA(1)
            if not(_la==15 or _la==73):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def implication(self):
            return self.getTypedRuleContext(StratagemDSLParser.ImplicationContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_expr

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpr" ):
                return visitor.visitExpr(self)
            else:
                return visitor.visitChildren(self)




    def expr(self):

        localctx = StratagemDSLParser.ExprContext(self, self._ctx, self.state)
        self.enterRule(localctx, 106, self.RULE_expr)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 609
            self.implication()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ImplicationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def orExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.OrExprContext,0)


        def IMPLIES(self):
            return self.getToken(StratagemDSLParser.IMPLIES, 0)

        def implication(self):
            return self.getTypedRuleContext(StratagemDSLParser.ImplicationContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_implication

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitImplication" ):
                return visitor.visitImplication(self)
            else:
                return visitor.visitChildren(self)




    def implication(self):

        localctx = StratagemDSLParser.ImplicationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 108, self.RULE_implication)
        try:
            self.state = 616
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,57,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 611
                self.orExpr(0)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 612
                self.orExpr(0)
                self.state = 613
                self.match(StratagemDSLParser.IMPLIES)
                self.state = 614
                self.implication()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OrExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def andExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.AndExprContext,0)


        def orExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.OrExprContext,0)


        def OR(self):
            return self.getToken(StratagemDSLParser.OR, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_orExpr

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOrExpr" ):
                return visitor.visitOrExpr(self)
            else:
                return visitor.visitChildren(self)



    def orExpr(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = StratagemDSLParser.OrExprContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 110
        self.enterRecursionRule(localctx, 110, self.RULE_orExpr, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 619
            self.andExpr(0)
            self._ctx.stop = self._input.LT(-1)
            self.state = 626
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,58,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    localctx = StratagemDSLParser.OrExprContext(self, _parentctx, _parentState)
                    self.pushNewRecursionContext(localctx, _startState, self.RULE_orExpr)
                    self.state = 621
                    if not self.precpred(self._ctx, 1):
                        from antlr4.error.Errors import FailedPredicateException
                        raise FailedPredicateException(self, "self.precpred(self._ctx, 1)")
                    self.state = 622
                    self.match(StratagemDSLParser.OR)
                    self.state = 623
                    self.andExpr(0) 
                self.state = 628
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,58,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class AndExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def comparison(self):
            return self.getTypedRuleContext(StratagemDSLParser.ComparisonContext,0)


        def andExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.AndExprContext,0)


        def AND(self):
            return self.getToken(StratagemDSLParser.AND, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_andExpr

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAndExpr" ):
                return visitor.visitAndExpr(self)
            else:
                return visitor.visitChildren(self)



    def andExpr(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = StratagemDSLParser.AndExprContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 112
        self.enterRecursionRule(localctx, 112, self.RULE_andExpr, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 630
            self.comparison()
            self._ctx.stop = self._input.LT(-1)
            self.state = 637
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,59,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    localctx = StratagemDSLParser.AndExprContext(self, _parentctx, _parentState)
                    self.pushNewRecursionContext(localctx, _startState, self.RULE_andExpr)
                    self.state = 632
                    if not self.precpred(self._ctx, 1):
                        from antlr4.error.Errors import FailedPredicateException
                        raise FailedPredicateException(self, "self.precpred(self._ctx, 1)")
                    self.state = 633
                    self.match(StratagemDSLParser.AND)
                    self.state = 634
                    self.comparison() 
                self.state = 639
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,59,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class ComparisonContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.op = None # Token

        def sumExpr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.SumExprContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.SumExprContext,i)


        def LT(self):
            return self.getToken(StratagemDSLParser.LT, 0)

        def LE(self):
            return self.getToken(StratagemDSLParser.LE, 0)

        def GT(self):
            return self.getToken(StratagemDSLParser.GT, 0)

        def GE(self):
            return self.getToken(StratagemDSLParser.GE, 0)

        def EQ(self):
            return self.getToken(StratagemDSLParser.EQ, 0)

        def NEQ(self):
            return self.getToken(StratagemDSLParser.NEQ, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_comparison

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComparison" ):
                return visitor.visitComparison(self)
            else:
                return visitor.visitChildren(self)




    def comparison(self):

        localctx = StratagemDSLParser.ComparisonContext(self, self._ctx, self.state)
        self.enterRule(localctx, 114, self.RULE_comparison)
        self._la = 0 # Token type
        try:
            self.state = 645
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,60,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 640
                self.sumExpr(0)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 641
                self.sumExpr(0)
                self.state = 642
                localctx.op = self._input.LT(1)
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 1107885508333142016) != 0)):
                    localctx.op = self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 643
                self.sumExpr(0)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SumExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.op = None # Token

        def productExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ProductExprContext,0)


        def sumExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.SumExprContext,0)


        def PLUS(self):
            return self.getToken(StratagemDSLParser.PLUS, 0)

        def MINUS(self):
            return self.getToken(StratagemDSLParser.MINUS, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_sumExpr

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSumExpr" ):
                return visitor.visitSumExpr(self)
            else:
                return visitor.visitChildren(self)



    def sumExpr(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = StratagemDSLParser.SumExprContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 116
        self.enterRecursionRule(localctx, 116, self.RULE_sumExpr, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 648
            self.productExpr(0)
            self._ctx.stop = self._input.LT(-1)
            self.state = 655
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,61,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    localctx = StratagemDSLParser.SumExprContext(self, _parentctx, _parentState)
                    self.pushNewRecursionContext(localctx, _startState, self.RULE_sumExpr)
                    self.state = 650
                    if not self.precpred(self._ctx, 1):
                        from antlr4.error.Errors import FailedPredicateException
                        raise FailedPredicateException(self, "self.precpred(self._ctx, 1)")
                    self.state = 651
                    localctx.op = self._input.LT(1)
                    _la = self._input.LA(1)
                    if not(_la==60 or _la==61):
                        localctx.op = self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()
                    self.state = 652
                    self.productExpr(0) 
                self.state = 657
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,61,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class ProductExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.op = None # Token

        def unaryExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.UnaryExprContext,0)


        def productExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ProductExprContext,0)


        def MUL(self):
            return self.getToken(StratagemDSLParser.MUL, 0)

        def DIV(self):
            return self.getToken(StratagemDSLParser.DIV, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_productExpr

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitProductExpr" ):
                return visitor.visitProductExpr(self)
            else:
                return visitor.visitChildren(self)



    def productExpr(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = StratagemDSLParser.ProductExprContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 118
        self.enterRecursionRule(localctx, 118, self.RULE_productExpr, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 659
            self.unaryExpr()
            self._ctx.stop = self._input.LT(-1)
            self.state = 666
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,62,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    localctx = StratagemDSLParser.ProductExprContext(self, _parentctx, _parentState)
                    self.pushNewRecursionContext(localctx, _startState, self.RULE_productExpr)
                    self.state = 661
                    if not self.precpred(self._ctx, 1):
                        from antlr4.error.Errors import FailedPredicateException
                        raise FailedPredicateException(self, "self.precpred(self._ctx, 1)")
                    self.state = 662
                    localctx.op = self._input.LT(1)
                    _la = self._input.LA(1)
                    if not(_la==62 or _la==63):
                        localctx.op = self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()
                    self.state = 663
                    self.unaryExpr() 
                self.state = 668
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,62,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class UnaryExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NOT(self):
            return self.getToken(StratagemDSLParser.NOT, 0)

        def unaryExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.UnaryExprContext,0)


        def MINUS(self):
            return self.getToken(StratagemDSLParser.MINUS, 0)

        def atom(self):
            return self.getTypedRuleContext(StratagemDSLParser.AtomContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_unaryExpr

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnaryExpr" ):
                return visitor.visitUnaryExpr(self)
            else:
                return visitor.visitChildren(self)




    def unaryExpr(self):

        localctx = StratagemDSLParser.UnaryExprContext(self, self._ctx, self.state)
        self.enterRule(localctx, 120, self.RULE_unaryExpr)
        try:
            self.state = 674
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [43]:
                self.enterOuterAlt(localctx, 1)
                self.state = 669
                self.match(StratagemDSLParser.NOT)
                self.state = 670
                self.unaryExpr()
                pass
            elif token in [61]:
                self.enterOuterAlt(localctx, 2)
                self.state = 671
                self.match(StratagemDSLParser.MINUS)
                self.state = 672
                self.unaryExpr()
                pass
            elif token in [41, 42, 68, 70, 71, 72, 73]:
                self.enterOuterAlt(localctx, 3)
                self.state = 673
                self.atom()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AtomContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LPAREN(self):
            return self.getToken(StratagemDSLParser.LPAREN, 0)

        def expr(self):
            return self.getTypedRuleContext(StratagemDSLParser.ExprContext,0)


        def RPAREN(self):
            return self.getToken(StratagemDSLParser.RPAREN, 0)

        def callExpr(self):
            return self.getTypedRuleContext(StratagemDSLParser.CallExprContext,0)


        def literal(self):
            return self.getTypedRuleContext(StratagemDSLParser.LiteralContext,0)


        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_atom

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtom" ):
                return visitor.visitAtom(self)
            else:
                return visitor.visitChildren(self)




    def atom(self):

        localctx = StratagemDSLParser.AtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 122, self.RULE_atom)
        try:
            self.state = 683
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,64,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 676
                self.match(StratagemDSLParser.LPAREN)
                self.state = 677
                self.expr()
                self.state = 678
                self.match(StratagemDSLParser.RPAREN)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 680
                self.callExpr()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 681
                self.literal()
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 682
                self.match(StratagemDSLParser.ID)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CallExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(StratagemDSLParser.ID, 0)

        def LPAREN(self):
            return self.getToken(StratagemDSLParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(StratagemDSLParser.RPAREN, 0)

        def argumentList(self):
            return self.getTypedRuleContext(StratagemDSLParser.ArgumentListContext,0)


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_callExpr

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCallExpr" ):
                return visitor.visitCallExpr(self)
            else:
                return visitor.visitChildren(self)




    def callExpr(self):

        localctx = StratagemDSLParser.CallExprContext(self, self._ctx, self.state)
        self.enterRule(localctx, 124, self.RULE_callExpr)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 685
            self.match(StratagemDSLParser.ID)
            self.state = 686
            self.match(StratagemDSLParser.LPAREN)
            self.state = 688
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 41)) & ~0x3f) == 0 and ((1 << (_la - 41)) & 8188329991) != 0):
                self.state = 687
                self.argumentList()


            self.state = 690
            self.match(StratagemDSLParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArgumentListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(StratagemDSLParser.ExprContext)
            else:
                return self.getTypedRuleContext(StratagemDSLParser.ExprContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(StratagemDSLParser.COMMA)
            else:
                return self.getToken(StratagemDSLParser.COMMA, i)

        def getRuleIndex(self):
            return StratagemDSLParser.RULE_argumentList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArgumentList" ):
                return visitor.visitArgumentList(self)
            else:
                return visitor.visitChildren(self)




    def argumentList(self):

        localctx = StratagemDSLParser.ArgumentListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 126, self.RULE_argumentList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 692
            self.expr()
            self.state = 697
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==51:
                self.state = 693
                self.match(StratagemDSLParser.COMMA)
                self.state = 694
                self.expr()
                self.state = 699
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LiteralContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return StratagemDSLParser.RULE_literal

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class StringLiteralContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def STRING(self):
            return self.getToken(StratagemDSLParser.STRING, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStringLiteral" ):
                return visitor.visitStringLiteral(self)
            else:
                return visitor.visitChildren(self)


    class TrueLiteralContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def TRUE(self):
            return self.getToken(StratagemDSLParser.TRUE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTrueLiteral" ):
                return visitor.visitTrueLiteral(self)
            else:
                return visitor.visitChildren(self)


    class NumberLiteralContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def INT(self):
            return self.getToken(StratagemDSLParser.INT, 0)
        def NUMBER(self):
            return self.getToken(StratagemDSLParser.NUMBER, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumberLiteral" ):
                return visitor.visitNumberLiteral(self)
            else:
                return visitor.visitChildren(self)


    class FalseLiteralContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a StratagemDSLParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FALSE(self):
            return self.getToken(StratagemDSLParser.FALSE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFalseLiteral" ):
                return visitor.visitFalseLiteral(self)
            else:
                return visitor.visitChildren(self)



    def literal(self):

        localctx = StratagemDSLParser.LiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 128, self.RULE_literal)
        try:
            self.state = 705
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [72]:
                localctx = StratagemDSLParser.StringLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 700
                self.match(StratagemDSLParser.STRING)
                pass
            elif token in [70]:
                localctx = StratagemDSLParser.NumberLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 701
                self.match(StratagemDSLParser.INT)
                pass
            elif token in [71]:
                localctx = StratagemDSLParser.NumberLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 702
                self.match(StratagemDSLParser.NUMBER)
                pass
            elif token in [41]:
                localctx = StratagemDSLParser.TrueLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 703
                self.match(StratagemDSLParser.TRUE)
                pass
            elif token in [42]:
                localctx = StratagemDSLParser.FalseLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 704
                self.match(StratagemDSLParser.FALSE)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[6] = self.propertyValue_sempred
        self._predicates[49] = self.bindingExpr_sempred
        self._predicates[55] = self.orExpr_sempred
        self._predicates[56] = self.andExpr_sempred
        self._predicates[58] = self.sumExpr_sempred
        self._predicates[59] = self.productExpr_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def propertyValue_sempred(self, localctx:PropertyValueContext, predIndex:int):
            if predIndex == 0:
                return (0 if localctx._INT is None else localctx._INT.line) * 100000 + (0 if localctx._INT is None else localctx._INT.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1
         

            if predIndex == 1:
                return (0 if localctx._NUMBER is None else localctx._NUMBER.line) * 100000 + (0 if localctx._NUMBER is None else localctx._NUMBER.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1
         

    def bindingExpr_sempred(self, localctx:BindingExprContext, predIndex:int):
            if predIndex == 2:
                return (0 if localctx._INT is None else localctx._INT.line) * 100000 + (0 if localctx._INT is None else localctx._INT.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1
         

            if predIndex == 3:
                return (0 if localctx._NUMBER is None else localctx._NUMBER.line) * 100000 + (0 if localctx._NUMBER is None else localctx._NUMBER.column) == (0 if localctx._MINUS is None else localctx._MINUS.line) * 100000 + (0 if localctx._MINUS is None else localctx._MINUS.column) + 1
         

    def orExpr_sempred(self, localctx:OrExprContext, predIndex:int):
            if predIndex == 4:
                return self.precpred(self._ctx, 1)
         

    def andExpr_sempred(self, localctx:AndExprContext, predIndex:int):
            if predIndex == 5:
                return self.precpred(self._ctx, 1)
         

    def sumExpr_sempred(self, localctx:SumExprContext, predIndex:int):
            if predIndex == 6:
                return self.precpred(self._ctx, 1)
         

    def productExpr_sempred(self, localctx:ProductExprContext, predIndex:int):
            if predIndex == 7:
                return self.precpred(self._ctx, 1)
         




