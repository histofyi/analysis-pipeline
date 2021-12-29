HETATOMS = [' CA', ' CD', ' CL', ' CO', ' CU', ' MG', ' NA', ' NI', ' ZN', '15P', '2LJ', 'ACT', 'EDO', 'FME', 'FMT', 'FUC', 'GOL', 'HOH', 'IOD', 'MAN', 'NA', 'NAG', 'P4G', 'P6G', 'PEG', 'PG4', 'Q81', 'S04', 'SEP', 'SO4']

AMINOACIDS = {
    "natural":{
        "translations":{
            "three_letter":{
                "ala":"a", 
                "arg":"r", 
                "asn":"n", 
                "asp":"d", 
                "cys":"c", 
                "glu":"e", 
                "gln":"q", 
                "gly":"g", 
                "his":"h", 
                "ile":"i", 
                "leu":"l", 
                "lys":"k", 
                "met":"m", 
                "phe":"f", 
                "pro":"p", 
                "ser":"s", 
                "thr":"t", 
                "trp":"w", 
                "tyr":"y", 
                "val":"v"
            },
            "one_letter":{
                "a":"ala", 
                "r":"arg", 
                "n":"asn", 
                "d":"asp", 
                "c":"cys", 
                "e":"glu", 
                "q":"gln", 
                "g":"gly", 
                "h":"his", 
                "i":"ile", 
                "l":"leu", 
                "k":"lys", 
                "m":"met", 
                "f":"phe", 
                "p":"pro", 
                "s":"ser", 
                "t":"thr", 
                "w":"trp", 
                "y":"tyr", 
                "v":"val"
            }
        }
    },
    "synthetic":{
        "three_letter": [],
        "one_letter": []
    }
}


CHAINS = {
        "class_i_alpha":{
            "length":275,
            "range":[-25,10],
            "features":["class", "i", "alpha"],
            "label":"class_i_alpha",
            "ui_text":"Class I alpha",
            "webglcolor":"0x77DDBB"
        },
        "truncated_class_i_alpha":{
            "length":180,
            "range":[-10,10],
            "features":["class", "i", "alpha"],
            "label":"truncated_class_i_alpha",
            "ui_text":"Class I alpha (truncated)",
            "webglcolor":"0x77DDBB"
        },
        "beta2m":{
            "length":95,
            "range":[-12,12],
            "features":["beta", "2", "microglobulin"],
            "label":"beta2m",
            "ui_text":"Beta 2 microglobulin",
            "webglcolor":"0xFF9955"
        },
        "class_ii_alpha":{
            "length":180,
            "range":[-10,10],
            "features":[],
            "label":"class_ii_alpha",
            "ui_text":"Class II alpha",
            "example":""
        },
        "class_ii_beta":{
            "length":180,
            "range":[-10,10],
            "features":[],
            "label":"class_ii_beta",
            "ui_text":"Class II beta",
            "example":""

        },
        "tcr_alpha":{
            "length":200,
            "range":[-10,10],
            "features":[],
            "label":"tcr_alpha",
            "ui_text":"T cell receptor alpha",
            "webglcolor":"0xFF44BB"
        },
        "tcr_beta":{
            "length":240,
            "range":[-10,10],
            "features":[],
            "label":"tcr_beta",
            "ui_text":"T cell receptor beta",
            "webglcolor":"0x99DD55"
        },
        "pre_tcr_beta":{
            "length":240,
            "range":[-10,10],
            "features":[],
            "label":"pre_tcr_beta",
            "ui_text":"pre T cell receptor beta",
            "webglcolor":"0x99DD55"
        },
        "tcr_gamma":{
            "length":200,
            "range":[-10,10],
            "features":[],
            "label":"tcr_gamma",
            "ui_text":"T cell receptor gamma",
            "webglcolor":"0xFF44BB"
        },
        "tcr_delta":{
            "length":240,
            "range":[-10,10],
            "features":[],
            "label":"tcr_delta",
            "ui_text":"T cell receptor delta",
            "webglcolor":"0x99DD55"
        },
        "peptide":{
            "length":9,
            "range":[-7,7],
            "features":["peptide"],
            "label":"peptide",
            "ui_text":"Unassigned peptide",
            "webglcolor":"0x908EA8"
        },
        "class_i_peptide":{
            "length":9,
            "range":[-7,7],
            "features":["peptide"],
            "label":"class_i_peptide",
            "ui_text":"Class I peptide",
            "webglcolor":"0x908EA8"
        },
        "class_i_peptide_nter":{
            "length":2,
            "range":[0,3],
            "features":[],
            "label":"class_i_peptide_nter",
            "ui_text":"Class I peptide N-terminal fragment",
            "webglcolor":"0x666666"
        },
        "class_i_peptide_cter":{
            "length":2,
            "range":[-1,1],
            "features":[],
            "label":"class_i_peptide_cter",
            "ui_text":"Class I peptide C-terminal fragment",
            "webglcolor":"0x666666"
        },
        "class_ii_peptide":{
            "length":11,
            "range":[-2,10],
            "features":[],
            "label":"class_ii_peptide",
            "ui_text":"Class II peptide"
        }

}


UNFINISHED_CHAINS = {
    "nk_receptor":{
        "features":[],
        "label":"nk_receptor",
        "ui_text":"NK receptor"
    },
    "accessory_molecule":{
        "features":[],
        "label":"accessory_molecule",
        "ui_text":"Accessory molecule"
    },
    "superantigen":{
        "features":[],
        "label":"superantigen",
        "ui_text":"Superantigen"
    },
    "tapasin_homologue":{
        "features":[],
        "label":"tapasin_homologue",
        "webglcolor":"0x666666"
    }
}


LOCI = {
    "homo_sapiens": {
        "class_i":{
            "alpha":["hla-a","hla-b","hla-c","hla-e","hla-f","hla-g"]
        },
        "class_ii":{
            "alpha":["hla-dra","hla-dpa","hla-dqa"],
            "beta":["hla-drb","hla-dpb","hla-dqb"]
        }
    },
    "mus_musculus": {
        "class_i":{
            "alpha":["h2-k","h2-d","h2-l"]
        },
        "class_ii":{
            "alpha":["h2-aalpha", "h2-ealpha"],
            "beta":["h2-abeta", "h2-ebeta"]
        }
    },
    "rat": {
        "class_i":{
            "alpha":["rano-a1","rano-a2","rano-a","rano-ba","rano-bb"]
        },
        "class_ii":{
            "alpha":["rano-da"],
            "beta":["rano-db1"]
        }
    },
    "pig":{
        "class_i":{
            "alpha":["sla-1","sla-2","sla-3","sla-6"]
        },
        "class_ii":{
            "alpha":["sla-dra","sla-dqa"],
            "beta":["sla-drb1","sla-drb2","sla-dqa"]
        }
    },
    "rhesus_macaque":{},
}

SPECIES = [
    "homo sapiens",
    "mus musculus",
    "rattus norvegicus",
    "sus scrofa",
    "macaca mulatta",
    "bos taurus",
    "felis catus",
    "pteropus alecto",
    "canis lupus familiaris",
    "equus caballus",
    "gallus gallus",
    "ailuropoda melanoleuca",
    "ginglymostoma cirratum",
    "anas platyrhynchos",
    "oryctolagus cuniculus",
    "anolis carolinensis"
]

SPECIES_OVERRIDES = {
    "7ji2":{
        "organism_scientific":"mus musculus",
        "organism_common":"mouse"
    },
    "7cpo":{
        "organism_scientific":"anolis carolinensis",
        "organism_common":"green anole lizard"
    },
    "6m2k":{
        "organism_scientific":"oryctolagus cuniculus",
        "organism_common":"rabit"
    },
    "6nca":{
        "organism_scientific":"homo sapiens",
        "organism_common":"human"
    },
    "6bxq":{
        "organism_scientific":"homo sapiens",
        "organism_common":"human"
    },
    "3czf":{
        "organism_scientific":"homo sapiens",
        "organism_common":"human"
    },
    "5xs3":{
        "organism_scientific":"homo sapiens",
        "organism_common":"human"
    },
    "6l9n":{
        "organism_scientific":"mus musculus",
        "organism_common":"mouse"
    },
    "6l9m":{
        "organism_scientific":"mus musculus",
        "organism_common":"mouse"
    },
    "5gsr":{
        "organism_scientific":"mus musculus",
        "organism_common":"mouse"
    }
}