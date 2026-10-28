import torch
import numpy as np
import pickle, json, time, re, sys, os
import networkx as nx
from multiprocessing import Pool
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import requests


def run_one_ep(design_name, ep):
    # print(design_name, ep)
    folder_dir = f'../rtl2cone/cone_code/'
    with open(f'{folder_dir}/{design_name}/{ep}.v', 'r') as f:
            lines = f.readlines()
    documents = ""
    ### get output signal name
    out_sig = ""
    for line in lines:
        out_re = re.findall(r'(\s+)(\S+)(\s+)<=', line)
        if out_re:
            out_sig = out_re[0][1]
            break
    if not out_sig:
        assert False, "No output signal found!"
    for line in lines:
        line = re.sub(r'module coi ', f'module {out_sig} ', line)
        line = re.sub(r'\n', '', line)

        documents += line

    
    url = ""
    headers = { 
    "Content-Type": "application/json", 
    "api-key": "" #Please change your KEY.
    }
    data = {"messages": [
                        {"role": "system", "content": "You are a professional VLSI designer and an expert at Verilog coding."},
                        {"role": "user", "content": f"I will provide you with a combinational Verilog design with multiple input and single output. Please use less than 300 words summarize the functionality of this Verilog design (based on the input/output/intermediate signal names, the computational operations, etc.). Here is the Verilog design: {documents}"},
                        ]
            }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.json()["choices"][0]["message"]["content"])
    summary = response.json()["choices"][0]["message"]["content"]
    if not os.path.exists(f"./cone_summary/{design_name}"):
        os.makedirs(f"./cone_summary/{design_name}")
    with open(f"./cone_summary/{design_name}/{ep}.txt", 'w') as f:
        f.write(summary)




def get_dataset(design_lst):

    for design in design_lst:
        print("Current design: ", design)
        with open (f"../dataset/reg_lst/{design}.json", 'r') as f:
            reg_lst = json.load(f)


        save_dir = f"./cone_summary/{design}"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        else:
            os.system(f"rm -rf {save_dir}")
            os.makedirs(save_dir)
    
        for ep in reg_lst:
            run_one_ep(design, ep)
            
    

if __name__ == '__main__':

    global design_lst_all
    design_lst_all = ['spi']
    get_dataset(design_lst_all)