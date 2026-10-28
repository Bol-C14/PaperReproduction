import argparse
import os
import ruamel_yaml as yaml
from accelerate import Accelerator
import torch
from transformers.optimization import (
    AdamW,
    get_polynomial_decay_schedule_with_warmup,
)

from dataset_proc.load_dataset import load_train_valid_dataset_stage_align, NetDataset, TextEmbedDataset, MyDataset

from models.model_pretrain import RTL_Fusion
from models.model_net import Net_Encoder
from models.loss_fn import TripletLoss

from accelerate import DistributedDataParallelKwargs

from torch.utils.tensorboard import SummaryWriter  


date ='pretrain_abl1_0826'
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

ddp_kwargs = DistributedDataParallelKwargs(find_unused_parameters=True)
accelerator = Accelerator(kwargs_handlers=[ddp_kwargs])


def main(args, config):

    max_epoch = config['schedular']['epochs']
    max_epoch = 50

    #### Dataset #### 
    accelerator.print("Loading Dataset ...")
    train_loader_align = load_train_valid_dataset_stage_align(batch_size=config['batch_size'], train_valid="train")
    valid_loader_align = load_train_valid_dataset_stage_align(batch_size=config['batch_size'], train_valid="valid")
    accelerator.print("Dataset Loaded!")


    #### Model ####
    rtl_fusion = RTL_Fusion(config=config, device=accelerator.device, accelerator=accelerator)
    net_enc = torch.load(f"./pretrain_model/pretrain_stage_0809/net_enc.50.pt")
    rtl_fusion.load_net_enc(net_enc)
    optimizer = AdamW([
        {'params': rtl_fusion.parameters(), 'lr': config['optimizer']['lr'], 'eps':config['optimizer']['eps'], 'weight_decay':config['optimizer']['weight_decay']},
    ])
    lr_scheduler = get_polynomial_decay_schedule_with_warmup(
        optimizer,
        num_warmup_steps=config['schedular']['warmup_updates'],
        num_training_steps=config['schedular']['total_updates']*max_epoch,
        lr_end=config['schedular']['lr_end'],
        power=config['schedular']['power'],
    )


    (
        rtl_fusion,
        net_enc,
        optimizer,
        train_loader_align,
        valid_loader_align,
        lr_scheduler,
    ) = accelerator.prepare(
        rtl_fusion,
        net_enc,
        optimizer,
        train_loader_align,
        valid_loader_align,
        lr_scheduler,
    )

    step = 0
    

    for epoch in range(max_epoch):
        epoch_loss_train, epoch_loss_valid = 0, 0
        epoch_loss_cl, epoch_loss_gtmae, epoch_loss_match = 0, 0, 0
        epoch_loss_mlm_mixup, epoch_loss_align  = 0, 0
        real_batch_loss = 0
        j = 0
        ### train ###

        graph_ori_lader_train, graph_pos_loader_train, graph_neg_loader_train,\
        summary_loader_train, text_ori_loader_train, text_neg_loader_train,\
        net_ori_loader, net_neg_loader = train_loader_align
        for idx, data in enumerate(zip(graph_ori_lader_train, graph_pos_loader_train, graph_neg_loader_train,\
                                        summary_loader_train, text_ori_loader_train, text_neg_loader_train,\
                                        net_ori_loader, net_neg_loader)):
            data_rtl = (data[0], data[1], data[2], data[3], data[4], data[5])
            data_net = (data[6], data[7])
            step += 1
            rtl_fusion.train()
            net_enc.train()

            loss_train, loss_cl, loss_gtmae, loss_mlm_m, loss_match, loss_align = rtl_fusion((data_rtl, data_net), mode='pretrain')

            accelerator.backward(loss_train)
            optimizer.step()
            optimizer.zero_grad()
            lr_scheduler.step()
            epoch_loss_train += loss_train.item()
            epoch_loss_cl += loss_cl.item()
            epoch_loss_gtmae += loss_gtmae.item()
            epoch_loss_mlm_mixup += loss_mlm_m.item()
            epoch_loss_match += loss_match.item()
            epoch_loss_align += loss_align.item()
            real_batch_loss += loss_train.item()
            
            if (idx+1) % accumulation_steps == 0:
                optimizer.step()
                optimizer.zero_grad()
                lr_scheduler.step()
                # val_loss = valid_network(encoder_rtl, text_enc, text_proj, val_rtl_loader, loss_fn_valid, lambda_cs, lambda_mae)
                accelerator.print(
                    f"Batch{j} train_loss={(real_batch_loss/accumulation_steps):.3f}"
                )
                j+=1
                real_batch_loss = 0
            

        ### valid ###
        with torch.no_grad():
            rtl_fusion.eval()
            net_enc.eval()
            graph_ori_lader_train, graph_pos_loader_train, graph_neg_loader_train,\
            summary_loader_train, text_ori_loader_train, text_neg_loader_train,\
            net_ori_loader, net_neg_loader = valid_loader_align
            for idx_val, data in enumerate(zip(graph_ori_lader_train, graph_pos_loader_train, graph_neg_loader_train,\
                                        summary_loader_train, text_ori_loader_train, text_neg_loader_train,\
                                        net_ori_loader, net_neg_loader)):
                data_rtl = (data[0], data[1], data[2], data[3], data[4], data[5])
                data_net = (data[6], data[7])
                loss_val, _, _, _, _, _ = rtl_fusion((data_rtl, data_net), mode='pretrain')
                epoch_loss_valid += loss_val.item()
            

        epoch_loss_train = epoch_loss_train/(idx+1)
        epoch_loss_valid = epoch_loss_valid/(idx_val+1)
        accelerator.print(f"Epoch {epoch + 1}/{max_epoch}, Total Train Loss: {epoch_loss_train}, Total Val Loss: {epoch_loss_valid}")
        
        writer.add_scalar('Epoch Train Loss', epoch_loss_train, epoch)
        writer.add_scalar('Epoch Valid Loss', epoch_loss_valid, epoch)
        writer.add_scalar('Epoch Train Loss CL', epoch_loss_cl, epoch)
        writer.add_scalar('Epoch Train Loss GTMAE', epoch_loss_gtmae, epoch)
        writer.add_scalar('Epoch Train Loss MLM', epoch_loss_mlm_mixup, epoch)
        writer.add_scalar('Epoch Train Loss Match', epoch_loss_match, epoch)
        writer.add_scalar('Epoch Train Loss Align', epoch_loss_align, epoch)


        ## save model every k epoch###
        k = 3
        if (epoch+1) % k == 0:
            accelerator.wait_for_everyone()
            unwrap_rtl_fusion = accelerator.unwrap_model(rtl_fusion)
            torch.save(unwrap_rtl_fusion, f"{model_save_dir}/rtl_fusion.{epoch}.pt")
            unwrap_net_enc = accelerator.unwrap_model(net_enc)
            torch.save(unwrap_net_enc, f"{model_save_dir}/net_enc.{epoch}.pt")





if __name__ == '__main__':
    log_dir = f'./log/log_{date}'
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    else:
        os.system(f'rm -r {log_dir}')
        os.mkdir(log_dir)

    model_save_dir = f"./pretrain_model/{date}"
    if not os.path.exists(model_save_dir):
        os.mkdir(model_save_dir)


    global writer
    writer = SummaryWriter(log_dir)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='./configs/Pretrain.yaml')

    args = parser.parse_args()

    config = yaml.load(open(args.config, 'r'), Loader=yaml.Loader)

    global accumulation_steps
    accumulation_steps = 128

    main(args, config)