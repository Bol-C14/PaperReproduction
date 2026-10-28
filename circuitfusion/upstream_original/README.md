# CircuitFusion: Multimodal Circuit Representation Learning for Agile Chip Design

## Installation
```
conda create -n ckt --file requirements.txt
conda activate ckt
```

 
## Circuit Data Collection (Folder: "data_collect")

* All the RTL designs used in our work are collected from open-source projects, their links are attached below:
    ```
    ITC99: https://iwls.org/iwls2005/benchmarks.html
    OpenCores: https://opencores.org/
    VexRiscv: https://github.com/SpinalHDL/VexRiscv
    Chipyard: https://github.com/ucb-bar/chipyard
    ```
* RTL circuits
    - Original RTL code folder: "./data_collect/rtl/dataset/ori/{design}.v"
    - The functionally equivalent RTL designs are generated through equivalent transformations using synthesis tools (e.g., Yosys+ABC), in folder: "./data_collect/rtl/dataset/ori/{design}.v"
    - Register list is extracted through timing report, in folder: "./data_collect/rtl/reg_lst/{design}.json"
* Netlist circuits
    - The RTL designs are synthesized using Synopsys Design Compiler into netlists, original netlist folder: "./data_collect/netlist/dataset/ori/{design}.syn.v" 
   - Equivalent netlists are generated through different constraints used in DC, in folder "./data_collect/netlist/dataset/pos/{design}.syn.v" 
  




## Multimodal and Multi-Stage Circuit Preprocessing and Alignment (Folder: "dara_collect")

* RTL preprocessing
    - Equivalent transformation using Yosys + ABC
        - Code: "data_collect/rtl/dataset/pos_transform.py"
        - Input: RTL Verilog file ("data_collect/rtl/dataset/ori")
        - Output: Equivalent RTL Verilog file ("data_collect/rtl/dataset/pos")
    - Entire RTL design to graph
        - Code: "data_collect/rtl/dataset/scr_design2graph/vlg_design2graph.py"
        - Input: RTL Verilog file ("data_collect/rtl/dataset/ori or pos or neg")
        - Output: RTL graph ("data_collect/rtl/dataset/rtl_graph")
    - Extract cone text from Verilog
        - Code: "data_collect/rtl/dataset/cone_extract.py"
        - Input: RTL Verilog file ("data_collect/rtl/dataset/ori or pos or neg")
        - Output: Cone RTL Verilog code text ("data_collect/rtl/dataset/cone" & "data_collect/rtl/rtl2code/cone_code" with soft link)
    - RTL cone to graph
        - Folder: "data_collect/rtl/rtl2graph"
        - Code: "data_collect/rtl/rtl2graph/scr/vlg_cone2graph.py"
        - Input: "data_collect/rtl/rtl2code/cone_code"
        - Output: "data_collect/rtl/rtl2graph/cone_graph"
    - RTL cone to summary
        - Folder: "data_collect/rtl/rtl2summary"
        - Code: "data_collect/rtl/rtl2summary/extract_summary.py"
        - Input: "data_collect/rtl/rtl2code/cone_code"
        - Output: "data_collect/rtl/rtl2summary/cone_summary"
    - Cone summary to embedding
        - Folder: "data_collect/rtl/rtl2summary"
        - Code: "data_collect/rtl/rtl2summary/summary2vec.py"
        - Input: "data_collect/rtl/rtl2summary/cone_summary"
        - Output: "data_collect/rtl/rtl2summary/cone_summary_vec"

* Netlist preprocessing
    - Entire netlist design to graph
        - Code: "data_collect/netlist/dataset/scr_net2graph/vlg_design2graph.py"
        - Input: netlist Verilog file ("data_collect/netlist/dataset/ori or pos or neg")
        - Output: netlist graph ("data_collect/netlist/dataset/netlist_graph")
    - Netlist to cone graph
        - Code: "data_collect/netlist/dataset/scr_net2graph/transform_net.py"
        - Input: netlist graph ("data_collect/netlist/dataset/netlist_graph")
        - Output: netlist cone graph ("data_collect/netlist/dataset/cone_graph")

* Cross-stage circuit alignment
  - The circuits are aligned through registers.
  - Each register backtrace all the logic until reaching all other registers --> cone of register, it can be obtained through timing report
  - The above preprocessed data are then processed into circuit dataset for the AI model, with code in "dataset"
    


## CircuitFusion Pre-training (Folder: "model/ckt_fusion")

### Pre-training 
```
cd ./model/ckt_fusion
python3 pretrain_align_all.py
```
 
### CircuitFusion model
- Folder "/model/ckt_fusion/models"
- Change configurations in "/model/ckt_fusion/configs"
- Model saved in "/model/ckt_fusion/pretrain_model"

## Evaluation on Downstream Tasks (Folder: "model/ckt_fusion")

### Cross-Stage Circuit Retrieval & Zero-Shot Inference 
* Retrieval based on the similarities between circuit embeddings
```
cd ./model/ckt_fusion
python3 infer.zero_shot.py
```

### Few-Shot Inference 
* Fine-tuning for downstream tasks
* Supervised training based on task-specific labels:
  ```
  cd ./model/ckt_fusion
  python3 finetune_slack.py
  python3 finetune_wns.py
  python3 finetune_tns.py
  python3 finetune_power.py
  python3 finetune_area.py
  ```

## Citation
If CircuitFusion could help your project, please cite our work:

```
@inproceedings{
    fang2025circuitfusion,
    title={Circuitfusion: multimodal circuit representation learning for agile chip design},
    author={Fang, Wenji and Liu, Shang and Wang, Jing and Xie, Zhiyao},
    booktitle={International Conference on Learning Representations (ICLR)},
    year={2025}
}
```